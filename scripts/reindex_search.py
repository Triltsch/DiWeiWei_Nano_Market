#!/usr/bin/env python
"""Rebuild the local Meilisearch index from published PostgreSQL nanos."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings  # noqa: E402
from app.modules.search.service import rebuild_search_index  # noqa: E402

DEFAULT_DATABASE_URL = "postgresql+asyncpg://diwei_user:diwei_password@localhost:5432/diwei_nano_market"


def _resolve_database_url() -> str:
    settings = get_settings()
    if settings.POSTGRES_USER and settings.POSTGRES_PASSWORD and settings.POSTGRES_DB:
        return (
            "postgresql+asyncpg://"
            f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/{settings.POSTGRES_DB}"
        )
    if settings.DATABASE_URL:
        if settings.DATABASE_URL.startswith("postgresql://"):
            return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return settings.DATABASE_URL
    return DEFAULT_DATABASE_URL


async def _main() -> int:
    engine = create_async_engine(_resolve_database_url())
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            result = await rebuild_search_index(session)
    finally:
        await engine.dispose()

    logging.info("Search index rebuilt: %s (%s documents)", result["index_name"], result["document_count"])
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(asyncio.run(_main()))