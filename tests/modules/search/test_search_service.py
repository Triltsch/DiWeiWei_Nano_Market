"""Tests for search service functionality.

Unit and integration tests for the search service, including parameter
validation, Meilisearch integration, Redis cache behavior, and degraded mode.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.search.service import (
    build_search_cache_key,
    invalidate_search_cache,
    search_nanos,
)


class TestSearchNanosService:
    """Tests for search_nanos service function."""

    @pytest.mark.asyncio
    async def test_search_missing_query(self):
        """Empty query is rejected with HTTP 400."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="", page=1, limit=20)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_page(self):
        """Page values below 1 are rejected with HTTP 400."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", page=0, limit=20)

        assert exc_info.value.status_code == 400
        assert "page" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_limit(self):
        """Limit outside 1..100 is rejected with HTTP 400."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", page=1, limit=150)

        assert exc_info.value.status_code == 400
        assert "limit" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_level(self):
        """Invalid competency levels are rejected with HTTP 400."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", level=5)

        assert exc_info.value.status_code == 400
        assert "level" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_duration(self):
        """Invalid duration filter values are rejected with HTTP 400."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", duration="invalid")

        assert exc_info.value.status_code == 400
        assert "duration" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_invalid_language(self):
        """Invalid language codes are rejected with HTTP 400."""
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await search_nanos(db=mock_db, query="python", language="EN")

        assert exc_info.value.status_code == 400
        assert "language" in exc_info.value.detail.lower()

    @pytest.mark.unit
    def test_build_search_cache_key_is_deterministic(self):
        """Cache key generation is deterministic and parameter-complete."""
        key_a = build_search_cache_key(
            query="python",
            category="Programming",
            level=2,
            duration="15-30",
            language="de",
            page=1,
            limit=20,
        )
        key_b = build_search_cache_key(
            query="python",
            category="Programming",
            level=2,
            duration="15-30",
            language="de",
            page=1,
            limit=20,
        )

        assert key_a == key_b
        assert "q=python" in key_a
        assert "category=Programming" in key_a
        assert "level=2" in key_a
        assert "duration=15-30" in key_a
        assert "language=de" in key_a
        assert "page=1" in key_a
        assert "limit=20" in key_a

    @pytest.mark.asyncio
    @patch("app.modules.search.service.get_redis")
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_cache_miss_then_store(self, mock_client_class, mock_get_redis):
        """On cache miss, service queries Meilisearch and stores response in Redis."""
        mock_db = AsyncMock(spec=AsyncSession)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

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

        result = await search_nanos(db=mock_db, query="python", page=1, limit=20)

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].title == "Python Basics"
        mock_client_instance.search.assert_called_once()
        mock_redis.setex.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.search.service.get_redis")
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_cache_hit_skips_meilisearch(self, mock_client_class, mock_get_redis):
        """On cache hit, service returns cached payload and skips Meilisearch call."""
        mock_db = AsyncMock(spec=AsyncSession)

        cached_payload = (
            '{"success":true,"data":[],"meta":{"pagination":{"current_page":1,'
            '"page_size":20,"total_results":0,"total_pages":0,"has_next_page":false,'
            '"has_prev_page":false},"query":{"search_query":"python","category":null,'
            '"level":null,"duration":null,"language":null}},"timestamp":"2026-03-16T12:34:56Z"}'
        )

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached_payload)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        result = await search_nanos(db=mock_db, query="python", page=1, limit=20)

        assert result.success is True
        assert len(result.data) == 0
        mock_client_class.assert_not_called()
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.modules.search.service.get_redis")
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_degraded_mode_when_redis_unavailable(
        self, mock_client_class, mock_get_redis
    ):
        """Redis outages do not fail API; service falls back to live Meilisearch search."""
        mock_db = AsyncMock(spec=AsyncSession)

        mock_get_redis.side_effect = RuntimeError("redis unavailable")

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
                    "thumbnail_url": None,
                }
            ],
            "estimatedTotalHits": 1,
        }

        result = await search_nanos(db=mock_db, query="python", page=1, limit=20)

        assert result.success is True
        assert len(result.data) == 1
        mock_client_instance.search.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.modules.search.service.get_redis")
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_pagination_calculation(self, mock_client_class, mock_get_redis):
        """Pagination metadata is correctly calculated from estimated total."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.search.return_value = {
            "hits": [{"id": "123", "title": f"Result {i}"} for i in range(20)],
            "estimatedTotalHits": 45,
        }

        mock_db = AsyncMock(spec=AsyncSession)

        result = await search_nanos(db=mock_db, query="test", page=1, limit=20)
        assert result.meta.pagination.current_page == 1
        assert result.meta.pagination.total_pages == 3
        assert result.meta.pagination.has_next_page is True
        assert result.meta.pagination.has_prev_page is False

        # Middle page should have both previous and next page
        result = await search_nanos(db=mock_db, query="test", page=2, limit=20)
        assert result.meta.pagination.current_page == 2
        assert result.meta.pagination.total_pages == 3
        assert result.meta.pagination.has_next_page is True
        assert result.meta.pagination.has_prev_page is True

        # Last page should have previous page but no next page
        result = await search_nanos(db=mock_db, query="test", page=3, limit=20)
        assert result.meta.pagination.current_page == 3
        assert result.meta.pagination.total_pages == 3
        assert result.meta.pagination.has_next_page is False
        assert result.meta.pagination.has_prev_page is True

    @pytest.mark.asyncio
    @patch("app.modules.search.service.get_redis")
    @patch("app.modules.search.service.MeilisearchClient")
    async def test_search_with_filters(self, mock_client_class, mock_get_redis):
        """Filters are passed through to Meilisearch client."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

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
            language="en",
            page=1,
            limit=20,
        )

        mock_client_instance.search.assert_called_once()
        call_kwargs = mock_client_instance.search.call_args.kwargs
        assert call_kwargs["query"] == "python"
        assert call_kwargs["category"] == "Programming"
        assert call_kwargs["level"] == 2
        assert call_kwargs["duration"] == "15-30"
        assert call_kwargs["language"] == "en"

    @pytest.mark.asyncio
    @patch("app.modules.search.service.get_redis")
    async def test_invalidate_search_cache_deletes_prefixed_keys(self, mock_get_redis):
        """Invalidation removes all configured search cache keys via scan_iter."""
        mock_redis = AsyncMock()

        async def _scan_iter(**_kwargs):
            for key in ["search:v1:a", "search:v1:b"]:
                yield key

        mock_redis.scan_iter = _scan_iter
        mock_redis.delete = AsyncMock(return_value=2)
        mock_get_redis.return_value = mock_redis

        deleted = await invalidate_search_cache(reason="test")

        assert deleted == 2
        mock_redis.delete.assert_awaited_once_with("search:v1:a", "search:v1:b")

    @pytest.mark.asyncio
    @patch("app.modules.search.service.get_redis")
    async def test_invalidate_search_cache_degraded_mode(self, mock_get_redis):
        """Invalidation returns 0 and does not raise when Redis is unavailable."""
        mock_get_redis.side_effect = RuntimeError("redis down")

        deleted = await invalidate_search_cache(reason="test")

        assert deleted == 0
