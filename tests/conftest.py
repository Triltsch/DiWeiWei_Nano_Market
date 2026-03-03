"""Pytest configuration and fixtures for testing"""

import asyncio
import os
import sys
import uuid
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import create_app
from app.models import Base, User
from app.modules.auth.service import verify_user_email
from app.redis_client import close_redis, get_redis


def pytest_configure(config):
    """Register custom pytest markers and load environment"""
    # Load .env file early before any imports of app modules
    try:
        from dotenv import load_dotenv

        load_dotenv(".env", override=True)
    except ImportError:
        # Fallback: manually parse .env file
        import re

        if os.path.exists(".env"):
            with open(".env") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        match = re.match(r"^([^=]+)=(.*)$", line)
                        if match:
                            key, value = match.groups()
                            # Remove quotes if present
                            value = value.strip('"')
                            os.environ[key] = value

    # Clear any cached settings to ensure fresh load from updated environment
    from app.config import get_settings

    get_settings.cache_clear()

    # Force reload of redis_client to pick up fresh settings
    import importlib

    if "app.redis_client" in sys.modules:
        importlib.reload(sys.modules["app.redis_client"])

    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires Docker PostgreSQL)"
    )
    config.addinivalue_line("markers", "unit: mark test as a unit test (uses in-memory SQLite)")


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
async def test_db_engine():
    """Create a test database engine for each test.

    Uses PostgreSQL if TEST_DB_URL environment variable is set (integration tests),
    otherwise uses in-memory SQLite (unit tests).
    """
    test_db_url = os.getenv("TEST_DB_URL")

    if test_db_url:
        # Integration test: use PostgreSQL
        engine = create_async_engine(
            test_db_url,
            echo=False,
        )
    else:
        # Unit test: use SQLite in-memory
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    async with engine.begin() as conn:
        # For PostgreSQL, drop all tables and enum types first to ensure clean state
        if test_db_url:
            await conn.run_sync(Base.metadata.drop_all)
            # Drop enum types that might exist from previous migrations
            await conn.execute(text("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT typname FROM pg_type WHERE typname IN 
                            ('userstatus', 'userrole', 'auditaction', 'consenttype', 
                             'nanostatus', 'nanoformat', 'competencylevel', 'licensetype')) 
                        LOOP
                            EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                        END LOOP;
                    END $$;
                    """))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # Clean up enum types after tests
        if test_db_url:
            await conn.execute(text("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT typname FROM pg_type WHERE typname IN 
                            ('userstatus', 'userrole', 'auditaction', 'consenttype', 
                             'nanostatus', 'nanoformat', 'competencylevel', 'licensetype')) 
                        LOOP
                            EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                        END LOOP;
                    END $$;
                    """))

    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine):
    """Create a fresh test database session for each test"""
    async_session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session

        # Cleanup: rolled back transactions and close session
        await session.rollback()
        await session.close()


@pytest.fixture
def app(db_session, mock_redis, mock_minio_storage):
    """Create test FastAPI app with mocked database, Redis, and MinIO storage"""
    from contextlib import asynccontextmanager

    from fastapi.middleware.cors import CORSMiddleware

    from app.config import get_settings
    from app.modules.audit.router import get_audit_router
    from app.modules.auth.router import get_auth_router
    from app.modules.upload.router import get_upload_router

    settings = get_settings()

    # Create app without lifespan (Redis is mocked for tests)
    @asynccontextmanager
    async def test_lifespan(app):
        yield

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=test_lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(get_auth_router())
    app.include_router(get_audit_router())
    app.include_router(get_upload_router())

    # Add endpoints
    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/")
    async def root() -> dict:
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def reset_redis_client(request):
    """Reset Redis client between async tests to avoid event loop conflicts

    The singleton Redis client can hold connections tied to a closed event loop
    when pytest-asyncio creates new loops between tests. This fixture ensures
    each test gets a fresh client.

    Skips reset for TestClient tests which use mocked Redis.
    """
    # Skip reset for tests using TestClient (they use mock_redis)
    if "client" in request.fixturenames:
        yield
        return

    import app.redis_client as redis_module

    # Reset the global client before each async test
    redis_module._redis_client = None
    yield
    # Clean up after test (if loop is still running)
    try:
        if redis_module._redis_client:
            await redis_module._redis_client.aclose()
            redis_module._redis_client = None
    except RuntimeError:
        # Loop already closed, just reset the reference
        redis_module._redis_client = None


@pytest.fixture
async def redis_client():
    """Get Redis client for explicit use in async tests

    Note: The reset_redis_client autouse fixture handles cleanup.
    """
    client = await get_redis()
    return client


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis operations for TestClient tests to avoid event loop conflicts"""
    from unittest.mock import AsyncMock, MagicMock

    storage: dict[str, str] = {}

    mock_client = MagicMock()
    mock_client.setex = AsyncMock(
        side_effect=lambda key, _ttl, value: storage.__setitem__(key, value)
    )
    mock_client.get = AsyncMock(side_effect=lambda key: storage.get(key))
    mock_client.exists = AsyncMock(side_effect=lambda key: 1 if key in storage else 0)
    mock_client.delete = AsyncMock(side_effect=lambda key: 1 if storage.pop(key, None) else 0)
    mock_client.close = AsyncMock()
    mock_client.aclose = AsyncMock()

    async def mock_get_redis():
        return mock_client

    async def mock_close_redis():
        pass

    # Mock the base redis_client module functions
    monkeypatch.setattr("app.redis_client.get_redis", mock_get_redis)
    monkeypatch.setattr("app.redis_client.close_redis", mock_close_redis)

    return mock_client


@pytest.fixture
def mock_minio_storage(monkeypatch):
    """Mock MinIO storage adapter for tests to avoid requiring MinIO server"""
    from unittest.mock import MagicMock

    # Create mock adapter that simulates successful uploads
    mock_adapter_class = MagicMock()
    mock_instance = MagicMock()

    # Mock upload_file to return a storage key
    def mock_upload_file(nano_id, file_content, filename, content_type="application/zip"):
        return f"nanos/{str(nano_id)}/content/{filename}"

    mock_instance.upload_file = mock_upload_file
    mock_instance.delete_file = MagicMock()
    mock_instance.get_file_url = MagicMock(return_value="http://minio:9000/file-url")
    mock_instance.object_exists = MagicMock(return_value=True)

    mock_adapter_class.return_value = mock_instance

    # Patch the MinIOStorageAdapter in both router and service modules
    monkeypatch.setattr("app.modules.upload.router.MinIOStorageAdapter", mock_adapter_class)
    monkeypatch.setattr("app.modules.upload.service.MinIOStorageAdapter", mock_adapter_class)

    return mock_instance


@pytest.fixture
def client(app):
    """Create test client (uses mocked Redis automatically via app fixture)"""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Create async HTTP test client"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user_data():
    """Test user registration data"""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "bio": "Test bio",
        "preferred_language": "de",
        "accept_terms": True,
        "accept_privacy": True,
    }


@pytest.fixture
async def test_invalid_passwords():
    """List of invalid passwords for testing validation"""
    return [
        "short",  # Too short
        "nouppercase123!",  # No uppercase
        "NoLowercase123!",  # No lowercase
        "NoSpecialChar123",  # No special character
        "NoDigits!",  # No digit
    ]


@pytest.fixture
async def verified_user_id(async_client, db_session, test_user_data):
    """Create and verify a test user, return their ID"""
    response = await async_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = UUID(response.json()["id"])

    # Verify the user email in the database
    await verify_user_email(db_session, user_id)
    return user_id


@pytest.fixture
async def verified_user(async_client, db_session, test_user_data) -> User:
    """Create and verify a test user, return the User object"""
    from sqlalchemy import select

    response = await async_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = UUID(response.json()["id"])

    # Verify the user email in the database
    await verify_user_email(db_session, user_id)

    # Fetch and return the user object
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one()
    return user


@pytest.fixture
async def admin_user(async_client, db_session) -> User:
    """Create and verify an admin user, return the User object"""
    from sqlalchemy import select

    from app.models import UserRole

    admin_data = {
        "email": f"admin_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"admin_{uuid.uuid4().hex[:8]}",
        "password": "AdminPass123!",
        "accept_terms": True,
        "accept_privacy": True,
    }

    response = await async_client.post("/api/v1/auth/register", json=admin_data)
    assert response.status_code == 201
    user_id = UUID(response.json()["id"])

    # Verify the user email and promote to admin
    await verify_user_email(db_session, user_id)

    # Promote user to admin role
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one()
    user.role = UserRole.ADMIN
    await db_session.commit()

    return user


@pytest.fixture
async def admin_token(async_client, admin_user: User) -> str:
    """Create and return access token for admin user"""
    # Login to get token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": admin_user.email,
            "password": "AdminPass123!",
        },
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]
