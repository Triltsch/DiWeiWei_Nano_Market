"""
Business logic for search functionality.

This module provides service functions for full-text search using Meilisearch,
including query processing, Redis caching (TTL 30 minutes), and pagination.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.search.schemas import SearchNano, SearchResponse
from app.redis_client import get_redis

settings = get_settings()
logger = logging.getLogger(__name__)


class MeilisearchClient:
    """Meilisearch API client for search operations."""

    def __init__(self, url: str, master_key: Optional[str] = None):
        """
        Initialize Meilisearch client.

        Args:
            url: Meilisearch server URL (e.g., http://localhost:7700)
            master_key: Master key for API authentication
        """
        try:
            import meilisearch
        except ImportError:
            raise ImportError(
                "meilisearch package not installed. Install with: pip install meilisearch"
            )

        self.client = meilisearch.Client(url, api_key=master_key)
        self.index_name = "nanos_v1"

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        level: Optional[int] = None,
        duration: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """
        Search for Nanos in Meilisearch.

        Args:
            query: Search query string
            category: Optional category filter
            level: Optional competency level filter (1, 2, or 3)
            duration: Optional duration filter ("0-15", "15-30", "30+")
            page: Page number (1-indexed)
            limit: Results per page

        Returns:
            Dictionary with search results and metadata

        Raises:
            HTTPException: If Meilisearch is unavailable
        """
        try:
            index = self.client.get_index(self.index_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service unavailable",
            ) from e

        # Build filter expressions for Meilisearch
        filters = []

        # Only published Nanos
        filters.append("status = 'published'")

        # Category filter — escape single quotes to prevent Meilisearch filter injection
        if category:
            safe_category = category.replace("'", "\\'")
            filters.append(f"category = '{safe_category}'")

        # Competency level filter
        if level is not None and level in [1, 2, 3]:
            filters.append(f"competency_level = {level}")

        # Duration filter
        if duration:
            if duration == "0-15":
                filters.append("duration_minutes >= 0 AND duration_minutes <= 15")
            elif duration == "15-30":
                filters.append("duration_minutes > 15 AND duration_minutes <= 30")
            elif duration == "30+":
                filters.append("duration_minutes > 30")

        filter_expression = " AND ".join(filters)
        offset = (page - 1) * limit

        try:
            search_params = {
                "q": query,
                "offset": offset,
                "limit": limit,
                "sort": ["_rank:desc", "average_rating:desc"],
                "filter": [filter_expression],
            }
            return index.search(**search_params)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search operation failed",
            ) from e


def build_search_cache_key(
    query: str,
    category: Optional[str],
    level: Optional[int],
    duration: Optional[str],
    page: int,
    limit: int,
) -> str:
    """Build a deterministic Redis cache key for search parameters."""
    key_params = {
        "q": query.strip(),
        "category": category or "",
        "level": "" if level is None else str(level),
        "duration": duration or "",
        "page": str(page),
        "limit": str(limit),
    }
    canonical = urlencode(sorted(key_params.items()))
    return f"{settings.SEARCH_CACHE_KEY_PREFIX}:{canonical}"


async def _get_cached_search_response(cache_key: str) -> Optional[SearchResponse]:
    """Fetch and deserialize search response from Redis cache."""
    try:
        redis_client = await get_redis()
        payload = await redis_client.get(cache_key)
        if not payload:
            return None

        logger.info("search_cache_hit", extra={"cache_key": cache_key})
        return SearchResponse.model_validate_json(payload)
    except Exception:
        logger.warning("search_cache_unavailable_on_get", extra={"cache_key": cache_key})
        return None


async def _set_cached_search_response(cache_key: str, response: SearchResponse) -> None:
    """Store search response in Redis cache with configured TTL."""
    try:
        redis_client = await get_redis()
        await redis_client.setex(
            cache_key,
            settings.SEARCH_CACHE_TTL_SECONDS,
            response.model_dump_json(),
        )
        logger.info("search_cache_store", extra={"cache_key": cache_key})
    except Exception:
        logger.warning("search_cache_unavailable_on_set", extra={"cache_key": cache_key})


async def invalidate_search_cache(reason: str) -> int:
    """Invalidate all cached search entries.

    This broad invalidation strategy is applied on Nano data changes to keep
    search results consistent. It is safe to call in degraded mode (Redis down).

    Args:
        reason: Context for observability/logging.

    Returns:
        Number of deleted cache keys.
    """
    try:
        redis_client = await get_redis()
        pattern = f"{settings.SEARCH_CACHE_KEY_PREFIX}:*"
        keys = await redis_client.keys(pattern)
        if not keys:
            return 0

        deleted = await redis_client.delete(*keys)
        logger.info(
            "search_cache_invalidate",
            extra={"reason": reason, "deleted_keys": int(deleted)},
        )
        return int(deleted)
    except Exception:
        logger.warning("search_cache_unavailable_on_invalidate", extra={"reason": reason})
        return 0


async def search_nanos(
    db: AsyncSession,
    query: str,
    category: Optional[str] = None,
    level: Optional[int] = None,
    duration: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> SearchResponse:
    """
    Search for Nanos with full-text search.

    Args:
        db: Database session
        query: Search query string (case-insensitive)
        category: Optional category name filter
        level: Optional competency level filter (1, 2, or 3)
        duration: Optional duration filter ("0-15", "15-30", "30+")
        page: Page number (1-indexed, default 1)
        limit: Results per page (default 20, max 100)

    Returns:
        SearchResponse with results and pagination metadata

    Raises:
        HTTPException: If search service is unavailable or query is invalid
    """
    _ = db

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page must be >= 1",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100",
        )

    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="query parameter is required and cannot be empty",
        )

    if level is not None and level not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="level must be 1 (Basic), 2 (Intermediate), or 3 (Advanced)",
        )

    if duration is not None and duration not in ["0-15", "15-30", "30+"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="duration must be one of: '0-15', '15-30', '30+'",
        )

    normalized_query = query.strip()
    cache_key = build_search_cache_key(
        query=normalized_query,
        category=category,
        level=level,
        duration=duration,
        page=page,
        limit=limit,
    )

    cached_response = await _get_cached_search_response(cache_key)
    if cached_response is not None:
        return cached_response

    logger.info("search_cache_miss", extra={"cache_key": cache_key})

    try:
        client = MeilisearchClient(settings.MEILI_URL, settings.MEILI_MASTER_KEY)
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service not configured",
        ) from e

    search_result = client.search(
        query=normalized_query,
        category=category,
        level=level,
        duration=duration,
        page=page,
        limit=limit,
    )

    hits = search_result.get("hits", [])
    estimated_total = search_result.get("estimatedTotalHits", 0)

    results: list[SearchNano] = []
    for hit in hits:
        try:
            published_at_value = hit.get("published_at")
            if not published_at_value:
                published_at_value = datetime.now(timezone.utc).isoformat()

            nano = SearchNano(
                id=UUID(hit.get("id")),
                title=hit.get("title"),
                description=hit.get("description"),
                creator=hit.get("creator"),
                duration_minutes=hit.get("duration_minutes"),
                competency_level=hit.get("competency_level"),
                category=hit.get("category"),
                format=hit.get("format"),
                average_rating=hit.get("average_rating"),
                rating_count=hit.get("rating_count"),
                published_at=published_at_value,
                thumbnail_url=hit.get("thumbnail_url"),
            )
            results.append(nano)
        except (ValueError, TypeError, ValidationError):
            continue

    total_pages = (estimated_total + limit - 1) // limit
    has_next_page = page < total_pages
    has_prev_page = page > 1

    response = SearchResponse(
        success=True,
        data=results,
        meta={
            "pagination": {
                "current_page": page,
                "page_size": limit,
                "total_results": estimated_total,
                "total_pages": total_pages,
                "has_next_page": has_next_page,
                "has_prev_page": has_prev_page,
            },
            "query": {
                "search_query": normalized_query,
                "category": category,
                "level": level,
                "duration": duration,
            },
        },
        timestamp=datetime.now(timezone.utc),
    )

    await _set_cached_search_response(cache_key, response)
    return response
