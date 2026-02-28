"""Pytest configuration and fixtures for testing"""

import asyncio
import os
import sys
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import create_app
from app.models import Base, User
from app.modules.auth.service import verify_user_email
from app.redis_client import close_redis, get_redis


def pytest_configure(config):
    """Register custom pytest markers"""
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
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

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
def app(db_session, mock_redis):
    """Create test FastAPI app with mocked database and Redis"""
    from contextlib import asynccontextmanager

    from fastapi.middleware.cors import CORSMiddleware

    from app.config import get_settings
    from app.modules.auth.router import get_auth_router

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
