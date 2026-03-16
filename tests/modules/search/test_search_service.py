"""
Tests for search service functionality.

Unit and integration tests for the search service, including parameter validation,
Meilisearch integration, and error handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.search.service import search_nanos


class TestSearchNanosService:
    """
    Integration tests for search_nanos service function.

    Tests parameter validation, service integration, and error handling.
    """

    @pytest.mark.asyncio
    async def test_search_missing_query(self):
        """
        Test that search fails when query parameter is missing or empty.

        Expected: HTTPException with 400 status is raised.
        """
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="", page=1, limit=20)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_page(self):
        """
        Test that search fails when page number is invalid (< 1).

        Expected: HTTPException with 400 status is raised.
        """
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", page=0, limit=20)

        assert exc_info.value.status_code == 400
        assert "page" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_limit(self):
        """
        Test that search fails when limit is outside valid range (1-100).

        Expected: HTTPException with 400 status is raised.
        """
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", page=1, limit=150)

        assert exc_info.value.status_code == 400
        assert "limit" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_level(self):
        """
        Test that search fails when competency level is invalid (not 1-3).

        Expected: HTTPException with 400 status is raised.
        """
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", level=5)

        assert exc_info.value.status_code == 400
        assert "level" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_duration(self):
        """
        Test that search fails when duration filter is invalid.

        Expected: HTTPException with 400 status is raised.
        """
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", duration="invalid")

        assert exc_info.value.status_code == 400
        assert "duration" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_successful(self, mock_client_class):
        """
        Test successful search with valid parameters.

        Expected: SearchResponse is returned with results and metadata.
        """
        # Mock the client and search results
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.search.return_value = {
            "hits": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "Python Basics",
                    "description": "Learn Python",
                    "creator": "Jane Doe",
                    "duration_minutes": 30,
                    "competency_level": 1,
                    "category": "Programming",
                    "format": "video",
                    "average_rating": 4.5,
                    "rating_count": 10,
                    "published_at": "2026-03-10T10:00:00Z",
                    "thumbnail_url": "https://example.com/thumb.jpg",
                }
            ],
            "estimatedTotalHits": 1,
        }

        mock_db = AsyncMock(spec=AsyncSession)

        result = await search_nanos(db=mock_db, query="python", page=1, limit=20)

        # Verify response structure
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].title == "Python Basics"
        assert result.data[0].creator == "Jane Doe"
        assert "pagination" in result.meta
        assert result.meta["pagination"]["current_page"] == 1
        assert result.meta["pagination"]["page_size"] == 20
        assert result.meta["pagination"]["total_results"] == 1
        assert result.timestamp is not None

    @pytest.mark.asyncio
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_pagination_calculation(self, mock_client_class):
        """
        Test that pagination metadata is correctly calculated.

        Expected: Pagination fields reflect proper page/total calculations.
        """
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.search.return_value = {
            "hits": [{"id": "123", "title": f"Result {i}"} for i in range(20)],
            "estimatedTotalHits": 45,  # 3 pages with 20 items
        }

        mock_db = AsyncMock(spec=AsyncSession)

        # Test first page
        result = await search_nanos(db=mock_db, query="test", page=1, limit=20)
        assert result.meta["pagination"]["current_page"] == 1
        assert result.meta["pagination"]["total_pages"] == 3
        assert result.meta["pagination"]["has_next_page"] is True
        assert result.meta["pagination"]["has_prev_page"] is False

        # Reset mock for next test
        mock_client_instance.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 45,
        }

        # Test middle page
        result = await search_nanos(db=mock_db, query="test", page=2, limit=20)
        assert result.meta["pagination"]["current_page"] == 2
        assert result.meta["pagination"]["total_pages"] == 3
        assert result.meta["pagination"]["has_next_page"] is True
        assert result.meta["pagination"]["has_prev_page"] is True

        # Test last page
        result = await search_nanos(db=mock_db, query="test", page=3, limit=20)
        assert result.meta["pagination"]["current_page"] == 3
        assert result.meta["pagination"]["total_pages"] == 3
        assert result.meta["pagination"]["has_next_page"] is False
        assert result.meta["pagination"]["has_prev_page"] is True

    @pytest.mark.asyncio
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_with_filters(self, mock_client_class):
        """
        Test search with category, level, and duration filters.

        Expected: Filters are passed to Meilisearch client and applied.
        """
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.search.return_value = {"hits": [], "estimatedTotalHits": 0}

        mock_db = AsyncMock(spec=AsyncSession)

        await search_nanos(
            db=mock_db,
            query="python",
            category="Programming",
            level=2,
            duration="15-30",
            page=1,
            limit=20,
        )

        # Verify filters were passed to client
        mock_client_instance.search.assert_called_once()
        call_kwargs = mock_client_instance.search.call_args.kwargs
        assert call_kwargs["query"] == "python"
        assert call_kwargs["category"] == "Programming"
        assert call_kwargs["level"] == 2
        assert call_kwargs["duration"] == "15-30"
