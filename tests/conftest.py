"""Pytest configuration and fixtures for testing"""

import asyncio
import os
import sys
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import create_app
from app.models import Base, User
from app.modules.auth.service import verify_user_email


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
def app(db_session):
    """Create test FastAPI app with mocked database"""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


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
async def verified_user_id(client, db_session, test_user_data):
    """Create and verify a test user, return their ID"""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = UUID(response.json()["id"])

    # Verify the user email in the database
    await verify_user_email(db_session, user_id)
    return user_id


@pytest.fixture
async def verified_user(client, db_session, test_user_data) -> User:
    """Create and verify a test user, return the User object"""
    from sqlalchemy import select

    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    user_id = UUID(response.json()["id"])

    # Verify the user email in the database
    await verify_user_email(db_session, user_id)

    # Fetch and return the user object
    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalar_one()
    return user
