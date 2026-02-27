"""Pytest configuration and fixtures for testing"""

import asyncio
import sys
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import create_app
from app.models import Base
from app.modules.auth.service import verify_user_email


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
async def test_db_engine():
    """Create a test database engine for each test"""
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
