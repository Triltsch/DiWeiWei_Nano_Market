"""
Business logic for search functionality.

This module provides service functions for full-text search using Meilisearch,
including query processing, filtering, and pagination.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.search.schemas import SearchNano, SearchResponse

settings = get_settings()


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

        # Combine filters with AND
        filter_expression = " AND ".join(filters) if filters else None

        # Calculate offset for pagination
        offset = (page - 1) * limit

        try:
            search_params = {
                "q": query,
                "offset": offset,
                "limit": limit,
                "sort": ["_rank:desc", "average_rating:desc"],  # Relevance + quality ranking
            }

            if filter_expression:
                search_params["filter"] = [filter_expression]

            result = index.search(**search_params)

            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search operation failed",
            ) from e


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

    # Validate pagination parameters
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

    # Validate level parameter
    if level is not None and level not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="level must be 1 (Basic), 2 (Intermediate), or 3 (Advanced)",
        )

    # Validate duration parameter
    if duration is not None and duration not in ["0-15", "15-30", "30+"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="duration must be one of: '0-15', '15-30', '30+'",
        )

    # Create Meilisearch client
    try:
        client = MeilisearchClient(settings.MEILI_URL, settings.MEILI_MASTER_KEY)
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service not configured",
        ) from e

    # Perform search in Meilisearch
    search_result = client.search(
        query=query.strip(),
        category=category,
        level=level,
        duration=duration,
        page=page,
        limit=limit,
    )

    # Extract hits and estimated total
    hits = search_result.get("hits", [])
    estimated_total = search_result.get("estimatedTotalHits", 0)

    # Build search results from hits
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
            # Skip malformed results
            continue

    # Calculate pagination metadata
    total_pages = (estimated_total + limit - 1) // limit  # Ceiling division
    has_next_page = page < total_pages
    has_prev_page = page > 1

    # Build response
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
                "search_query": query,
                "category": category,
                "level": level,
                "duration": duration,
            },
        },
        timestamp=datetime.now(timezone.utc),
    )

    return response
