"""
Router for search endpoints.

This module provides the API endpoint for full-text search functionality
using Meilisearch.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.search.schemas import SearchResponse
from app.modules.search.service import search_nanos


def get_search_router(prefix: str = "/api/v1/search", tags: list[str] | None = None) -> APIRouter:
    """
    Create and configure the search router.

    Args:
        prefix: URL prefix for all search endpoints
        tags: OpenAPI tags for documentation

    Returns:
        Configured APIRouter instance
    """
    if tags is None:
        tags = ["Search"]

    router = APIRouter(prefix=prefix, tags=tags)

    @router.get(
        "",
        response_model=SearchResponse,
        summary="Search for Nanos",
        description="""
        Full-text search for published Nano learning units.

        **Query Parameters:**
        - `q`: Search query (required, case-insensitive, supports partial matches)
        - `category`: Optional category filter (exact match)
        - `level`: Optional competency level filter (1=Basic, 2=Intermediate, 3=Advanced)
        - `duration`: Optional duration filter (0-15, 15-30, or 30+ minutes)
        - `language`: Optional content language filter (ISO 639-1, e.g. `de`, `en`)
        - `page`: Page number (1-indexed, default 1)
        - `limit`: Results per page (default 20, max 100)

        **Returns:**
        - List of published Nanos matching the search criteria
        - Sorted by relevance (Meilisearch ranking) and average rating
        - Pagination metadata included

        **Error Cases:**
        - 400: Invalid query parameters
        - 503: Search service unavailable
        """,
        responses={
            200: {
                "description": "Search results with pagination metadata",
                "content": {
                    "application/json": {
                        "example": {
                            "success": True,
                            "data": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "title": "Excel Basics",
                                    "description": "Learn Excel fundamentals",
                                    "creator": "John Doe",
                                    "duration_minutes": 25,
                                    "competency_level": 1,
                                    "category": "Office",
                                    "format": "video",
                                    "average_rating": 4.5,
                                    "rating_count": 12,
                                    "published_at": "2026-03-10T10:00:00Z",
                                    "thumbnail_url": "https://...",
                                }
                            ],
                            "meta": {
                                "pagination": {
                                    "current_page": 1,
                                    "page_size": 20,
                                    "total_results": 145,
                                    "total_pages": 8,
                                    "has_next_page": True,
                                    "has_prev_page": False,
                                },
                                "query": {
                                    "search_query": "excel",
                                    "category": None,
                                    "level": None,
                                    "duration": None,
                                    "language": None,
                                },
                            },
                            "timestamp": "2026-03-16T12:34:56Z",
                        }
                    }
                },
            },
            400: {"description": "Invalid query parameters"},
            503: {"description": "Search service unavailable (Meilisearch)"},
        },
    )
    async def search(
        q: Annotated[str, Query(min_length=1, description="Search query (required)")],
        category: Annotated[
            Optional[str], Query(description="Optional category filter (exact match)")
        ] = None,
        level: Annotated[
            Optional[int], Query(ge=1, le=3, description="Optional competency level (1-3)")
        ] = None,
        duration: Annotated[
            Optional[str],
            Query(
                pattern=r"^(0-15|15-30|30\+)$",
                description="Optional duration filter (0-15, 15-30, or 30+)",
            ),
        ] = None,
        language: Annotated[
            Optional[str],
            Query(
                pattern=r"^[a-z]{2}$",
                description="Optional content language filter (ISO 639-1, e.g. de, en)",
            ),
        ] = None,
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 20,
        db: AsyncSession = Depends(get_db),
    ) -> SearchResponse:
        """Search for Nanos using full-text search with filters."""
        result = await search_nanos(
            db=db,
            query=q,
            category=category,
            level=level,
            duration=duration,
            language=language,
            page=page,
            limit=limit,
        )
        return result

    return router
