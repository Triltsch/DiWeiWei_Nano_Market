#!/usr/bin/env python
"""
Database initialization script.

Creates database schema from SQLAlchemy models.
Run this after configuring your database connection before starting the application.

Usage:
    python scripts/init_db.py

Environment:
    DATABASE_URL: PostgreSQL connection string (or TEST_DB_URL for Docker Compose)
    Example: postgresql+asyncpg://user:password@localhost:5433/diweiwei_test
"""

import asyncio
import logging
import sys
from pathlib import Path

import sqlalchemy.exc

# Add project root to path so imports work when running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.database import engine
from app.models import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def init_db() -> bool:
    """Initialize database schema.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        settings = get_settings()
        logger.info(f"Initializing database: {settings.DATABASE_URL.split('@')[0]}@...")

        async with engine.begin() as conn:
            logger.info("Creating database schema...")
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database schema created successfully!")
        logger.info("\nTables created:")
        logger.info("  - users")
        logger.info("  - audit_logs (future)")
        logger.info("\nYou can now start the application:")
        logger.info("  python -m uvicorn app.main:app --reload")

        return True

    except sqlalchemy.exc.ArgumentError as e:
        logger.error(f"❌ Database configuration error: {e}")
        logger.error("\nPlease set DATABASE_URL or TEST_DB_URL environment variable")
        logger.error("Example:")
        logger.error(
            "  TEST_DB_URL=postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"
        )
        return False

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        logger.error("\nCommon causes:")
        logger.error("  1. PostgreSQL server not running")
        logger.error("  2. Invalid database URL")
        logger.error("  3. Database credentials wrong")
        logger.error("  4. Database doesn't exist")
        return False

    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(init_db())
    sys.exit(0 if success else 1)
