"""Business logic for search functionality.

This module provides read and indexing flows for Meilisearch-backed discovery,
including browse/search requests, Redis caching, and full index rebuilds from
published PostgreSQL data.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Category, Nano, NanoCategoryAssignment, NanoStatus, User
from app.modules.search.schemas import SearchNano, SearchResponse
from app.redis_client import get_redis

settings = get_settings()
logger = logging.getLogger(__name__)

MEILI_TASK_POLL_INTERVAL_SECONDS = 0.25
MEILI_TASK_MAX_POLLS = 60
MEILI_FILTERABLE_ATTRIBUTES = [
    "status",
    "category",
    "competency_level",
    "duration_minutes",
    "language",
]
MEILI_SORTABLE_ATTRIBUTES = ["average_rating", "published_at", "download_count"]


def _cache_key_hash(cache_key: str) -> str:
    """Return a short hash for safe cache key logging without raw user input."""
    return sha256(cache_key.encode("utf-8")).hexdigest()[:12]


def _meili_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.MEILI_MASTER_KEY:
        headers["Authorization"] = f"Bearer {settings.MEILI_MASTER_KEY}"
    return headers


async def _meili_request(path: str, *, method: str = "GET", payload: Any = None) -> tuple[int, Any]:
    def _execute_request() -> tuple[int, Any]:
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        request = Request(
            f"{settings.MEILI_URL.rstrip('/')}{path}",
            data=body,
            headers=_meili_headers(),
            method=method,
        )

        try:
            with urlopen(request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
                return response.status, json.loads(response_body) if response_body else None
        except HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            parsed_body: Any
            try:
                parsed_body = json.loads(response_body) if response_body else None
            except json.JSONDecodeError:
                parsed_body = response_body
            return error.code, parsed_body

    return await asyncio.to_thread(_execute_request)


async def _wait_for_meili_task(task_uid: int, *, ignore_index_not_found: bool = False) -> None:
    for _ in range(MEILI_TASK_MAX_POLLS):
        response_status, payload = await _meili_request(f"/tasks/{task_uid}")
        if response_status >= 400:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Search task lookup failed: {payload}",
            )

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"Unexpected response from search backend while polling task "
                    f"{task_uid}: {payload!r}"
                ),
            )

        task_status = payload.get("status")
        if task_status == "succeeded":
            return
        if task_status == "failed":
            error = payload.get("error")
            if (
                ignore_index_not_found
                and isinstance(error, dict)
                and error.get("code") == "index_not_found"
            ):
                return
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Search indexing task failed: {payload}",
            )

        await asyncio.sleep(MEILI_TASK_POLL_INTERVAL_SECONDS)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Timed out waiting for search indexing task",
    )


def _task_uid_from_response(payload: dict[str, Any]) -> int:
    task_uid = payload.get("taskUid")
    if not isinstance(task_uid, int):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Invalid Meilisearch task response: {payload}",
        )
    return task_uid


async def _build_search_documents(db: AsyncSession) -> list[dict[str, Any]]:
    nano_result = await db.execute(
        select(Nano, User.username)
        .outerjoin(User, Nano.creator_id == User.id)
        .where(Nano.status == NanoStatus.PUBLISHED)
        .order_by(Nano.average_rating.desc(), Nano.published_at.desc(), Nano.id.desc())
    )
    nano_rows = nano_result.all()
    if not nano_rows:
        return []

    nano_ids = [nano.id for nano, _ in nano_rows]
    category_result = await db.execute(
        select(NanoCategoryAssignment.nano_id, Category.name)
        .join(Category, NanoCategoryAssignment.category_id == Category.id)
        .where(NanoCategoryAssignment.nano_id.in_(nano_ids))
        .order_by(
            NanoCategoryAssignment.nano_id, NanoCategoryAssignment.rank.asc(), Category.name.asc()
        )
    )

    primary_categories: dict[UUID, str] = {}
    for nano_id, category_name in category_result.all():
        primary_categories.setdefault(nano_id, category_name)

    documents: list[dict[str, Any]] = []
    for nano, creator_username in nano_rows:
        published_at = nano.published_at or nano.updated_at or nano.uploaded_at
        documents.append(
            {
                "id": str(nano.id),
                "title": nano.title,
                "description": nano.description,
                "creator": creator_username,
                "duration_minutes": nano.duration_minutes,
                "competency_level": int(nano.competency_level),
                "category": primary_categories.get(nano.id),
                "format": nano.format.value.lower(),
                "average_rating": float(nano.average_rating),
                "rating_count": nano.rating_count,
                "published_at": published_at.isoformat() if published_at else None,
                "thumbnail_url": nano.thumbnail_url,
                "status": nano.status.value,
                "language": nano.language,
                "download_count": nano.download_count,
            }
        )

    return documents


async def rebuild_search_index(
    db: AsyncSession, index_name: Optional[str] = None
) -> dict[str, Any]:
    """Rebuild the configured Meilisearch index from published PostgreSQL nanos."""
    target_index = index_name or settings.MEILI_INDEX_UID
    documents = await _build_search_documents(db)

    try:
        delete_status, delete_payload = await _meili_request(
            f"/indexes/{target_index}", method="DELETE"
        )
        if delete_status == 202:
            await _wait_for_meili_task(
                _task_uid_from_response(delete_payload),
                ignore_index_not_found=True,
            )
        elif delete_status != 404:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Search index deletion failed: {delete_payload}",
            )

        create_status, create_payload = await _meili_request(
            "/indexes",
            method="POST",
            payload={"uid": target_index, "primaryKey": "id"},
        )
        if create_status >= 400:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Search index creation failed: {create_payload}",
            )
        await _wait_for_meili_task(_task_uid_from_response(create_payload))

        filterable_status, filterable_payload = await _meili_request(
            f"/indexes/{target_index}/settings/filterable-attributes",
            method="PUT",
            payload=MEILI_FILTERABLE_ATTRIBUTES,
        )
        if filterable_status >= 400:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Search filterable settings update failed: {filterable_payload}",
            )
        await _wait_for_meili_task(_task_uid_from_response(filterable_payload))

        sortable_status, sortable_payload = await _meili_request(
            f"/indexes/{target_index}/settings/sortable-attributes",
            method="PUT",
            payload=MEILI_SORTABLE_ATTRIBUTES,
        )
        if sortable_status >= 400:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Search sortable settings update failed: {sortable_payload}",
            )
        await _wait_for_meili_task(_task_uid_from_response(sortable_payload))

        documents_status, documents_payload = await _meili_request(
            f"/indexes/{target_index}/documents",
            method="POST",
            payload=documents,
        )
        if documents_status >= 400:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Search document upload failed: {documents_payload}",
            )
        await _wait_for_meili_task(_task_uid_from_response(documents_payload))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search indexing unavailable",
        ) from error

    await invalidate_search_cache(reason="search_reindex")
    logger.info(
        "search_index_rebuilt", extra={"index_name": target_index, "documents": len(documents)}
    )
    return {"index_name": target_index, "document_count": len(documents)}


class MeilisearchClient:
    """Meilisearch API client for search operations."""

    def __init__(
        self,
        url: str,
        master_key: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        """
        Initialize Meilisearch client.

        Args:
            url: Meilisearch server URL (e.g., http://localhost:7700)
            master_key: Master key for API authentication
            index_name: Optional target index UID (defaults to configured setting)
        """
        try:
            import meilisearch
        except ImportError:
            raise ImportError(
                "meilisearch package not installed. Install with: pip install meilisearch"
            )

        self.client = meilisearch.Client(url, api_key=master_key)
        self.index_name = index_name or settings.MEILI_INDEX_UID

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        level: Optional[int] = None,
        duration: Optional[str] = None,
        language: Optional[str] = None,
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
            language: Optional language filter (ISO 639-1 code, e.g. de, en)
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

        # Language filter
        if language:
            safe_language = language.replace("'", "\\'")
            filters.append(f"language = '{safe_language}'")

        filter_expression = " AND ".join(filters)
        offset = (page - 1) * limit

        try:
            search_params = {
                "offset": offset,
                "limit": limit,
                "sort": ["average_rating:desc"],
                "filter": filter_expression,
            }
            return index.search(query, search_params)
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
    language: Optional[str],
    page: int,
    limit: int,
) -> str:
    """Build a deterministic Redis cache key for search parameters."""
    key_params = {
        "q": query.strip(),
        "category": category or "",
        "level": "" if level is None else str(level),
        "duration": duration or "",
        "language": language or "",
        "page": str(page),
        "limit": str(limit),
    }
    canonical = urlencode(sorted(key_params.items()))
    return f"{settings.SEARCH_CACHE_KEY_PREFIX}:{canonical}"


async def _get_cached_search_response(cache_key: str) -> Optional[SearchResponse]:
    """Fetch and deserialize search response from Redis cache."""
    cache_key_hash = _cache_key_hash(cache_key)
    try:
        redis_client = await get_redis()
        payload = await redis_client.get(cache_key)
        if not payload:
            return None

        logger.info("search_cache_hit", extra={"cache_key_hash": cache_key_hash})
        return SearchResponse.model_validate_json(payload)
    except Exception:
        logger.warning("search_cache_unavailable_on_get", extra={"cache_key_hash": cache_key_hash})
        return None


async def _set_cached_search_response(cache_key: str, response: SearchResponse) -> None:
    """Store search response in Redis cache with configured TTL."""
    cache_key_hash = _cache_key_hash(cache_key)
    try:
        redis_client = await get_redis()
        await redis_client.setex(
            cache_key,
            settings.SEARCH_CACHE_TTL_SECONDS,
            response.model_dump_json(),
        )
        logger.info("search_cache_store", extra={"cache_key_hash": cache_key_hash})
    except Exception:
        logger.warning("search_cache_unavailable_on_set", extra={"cache_key_hash": cache_key_hash})


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
        deleted = 0
        batch: list[str] = []

        async for key in redis_client.scan_iter(match=pattern, count=200):
            batch.append(key)
            if len(batch) >= 200:
                deleted += int(await redis_client.delete(*batch))
                batch = []

        if batch:
            deleted += int(await redis_client.delete(*batch))

        logger.info(
            "search_cache_invalidate",
            extra={"reason": reason, "deleted_keys": deleted},
        )
        return deleted
    except Exception:
        logger.warning("search_cache_unavailable_on_invalidate", extra={"reason": reason})
        return 0


async def search_nanos(
    db: AsyncSession,
    query: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[int] = None,
    duration: Optional[str] = None,
    language: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> SearchResponse:
    """
    Search for Nanos with full-text search.

    Args:
        db: Database session
        query: Optional search query string (case-insensitive). Empty query browses published nanos.
        category: Optional category name filter
        level: Optional competency level filter (1, 2, or 3)
        duration: Optional duration filter ("0-15", "15-30", "30+")
        language: Optional ISO 639-1 language filter
        page: Page number (1-indexed, default 1)
        limit: Results per page (default 20, max 100)

    Returns:
        SearchResponse with results and pagination metadata

    Raises:
        HTTPException: If search service is unavailable or query is invalid
    """
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

    if language is not None and (
        len(language) != 2 or not language.isalpha() or not language.islower()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="language must be a two-letter lowercase ISO 639-1 code",
        )

    normalized_query = query.strip() if query else ""
    cache_key = build_search_cache_key(
        query=normalized_query,
        category=category,
        level=level,
        duration=duration,
        language=language,
        page=page,
        limit=limit,
    )

    cached_response = await _get_cached_search_response(cache_key)
    if cached_response is not None:
        return cached_response

    logger.info("search_cache_miss", extra={"cache_key_hash": _cache_key_hash(cache_key)})

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
        language=language,
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
                "language": language,
            },
        },
        timestamp=datetime.now(timezone.utc),
    )

    await _set_cached_search_response(cache_key, response)
    return response
