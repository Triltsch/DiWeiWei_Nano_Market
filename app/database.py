"""Database configuration and session management"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Validate database URL configuration
if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL must be set. Set one of:\n"
        "  - DATABASE_URL environment variable (production/development)\n"
        "  - TEST_DB_URL environment variable (Docker Compose on port 5433)\n"
        "  - .env file with DATABASE_URL\n"
        "Example for Docker Compose:\n"
        "  TEST_DB_URL=postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"
    )

logger.info(
    f"Initializing database with: "
    f"{settings.DATABASE_URL.split('@')[0]}@{settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'sqlite'}"
)

# Create async engine for PostgreSQL
engine_options: dict = {
    "echo": settings.DEBUG,
}

if settings.ENV == "test":
    engine_options["poolclass"] = NullPool

# Convert postgresql:// to postgresql+asyncpg:// for async support
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

try:
    engine = create_async_engine(
        database_url,
        **engine_options,
    )
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise ValueError(
        f"Invalid database configuration: {e}\n"
        f"Database URL: {settings.DATABASE_URL}\n"
        f"Check that your database is accessible and the connection string is correct."
    ) from e

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.

    Yields:
        AsyncSession: Database session instance
    """
    async with async_session() as session:
        yield session
