"""Database configuration and session management"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# Create async engine for PostgreSQL
engine_options: dict = {
    "echo": settings.DEBUG,
}

if settings.ENV == "test":
    engine_options["poolclass"] = NullPool

engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    **engine_options,
)

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
