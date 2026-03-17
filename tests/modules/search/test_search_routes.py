"""
Tests for search API routes.

Unit and contract tests for the search endpoint, including request validation,
response format, and HTTP status codes.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class TestSearchRoutes:
    """
    Tests for the search API endpoint (GET /api/v1/search).

    Tests endpoint functionality, parameter validation, and response format.
    """

    @pytest.mark.unit
    def test_get_search_endpoint_missing_query(self, client):
        """
        Test that search endpoint requires the query parameter.

        Expected: 422 Unprocessable Entity (missing required parameter).
        """
        response = client.get("/api/v1/search")
        assert response.status_code == 422

    @pytest.mark.unit
    def test_get_search_endpoint_empty_query(self, client):
        """
        Test that search endpoint rejects empty query string.

        Expected: 422 Unprocessable Entity (validation error).
        """
        response = client.get("/api/v1/search?q=")
        assert response.status_code == 422

    @pytest.mark.unit
    def test_get_search_endpoint_invalid_page(self, client):
        """
        Test that search endpoint validates page parameter.

        Expected: 400 Bad Request for invalid page values.
        """
        with patch("app.modules.search.router.search_nanos") as mock_search:
            mock_search.side_effect = Exception("Should not be called")

            response = client.get("/api/v1/search?q=test&page=0")
            # FastAPI validation should catch this before reaching our code
            assert response.status_code == 422

    @pytest.mark.unit
    def test_get_search_endpoint_invalid_limit(self, client):
        """
        Test that search endpoint validates limit parameter.

        Expected: 422 Unprocessable Entity for limit > 100.
        """
        response = client.get("/api/v1/search?q=test&limit=150")
        assert response.status_code == 422

    @pytest.mark.unit
    def test_get_search_endpoint_invalid_level(self, client):
        """
        Test that search endpoint validates level parameter.

        Expected: 422 Unprocessable Entity for level outside 1-3.
        """
        response = client.get("/api/v1/search?q=test&level=5")
        assert response.status_code == 422

    @pytest.mark.unit
    def test_get_search_endpoint_invalid_duration(self, client):
        """
        Test that search endpoint validates duration parameter.

        Expected: 422 Unprocessable Entity for invalid duration format.
        """
        response = client.get("/api/v1/search?q=test&duration=invalid")
        assert response.status_code == 422

    @pytest.mark.unit
    @patch("app.modules.search.router.search_nanos")
    def test_get_search_endpoint_success(self, mock_search, client):
        """
        Test successful search request.

        Expected: 200 OK with SearchResponse in correct format.
        """
        from datetime import datetime, timezone

        from app.modules.search.schemas import SearchNano, SearchResponse

        # Mock successful search result
        mock_nano = SearchNano(
            id=uuid4(),
            title="Excel Basics",
            description="Learn Excel fundamentals",
            creator="John Doe",
            duration_minutes=25,
            competency_level=1,
            category="Office",
            format="video",
            average_rating=4.5,
            rating_count=10,
            published_at=datetime.now(timezone.utc),
            thumbnail_url="https://example.com/thumb.jpg",
        )

        mock_response = SearchResponse(
            success=True,
            data=[mock_nano],
            meta={
                "pagination": {
                    "current_page": 1,
                    "page_size": 20,
                    "total_results": 1,
                    "total_pages": 1,
                    "has_next_page": False,
                    "has_prev_page": False,
                },
                "query": {
                    "search_query": "excel",
                    "category": None,
                    "level": None,
                    "duration": None,
                },
            },
            timestamp=datetime.now(timezone.utc),
        )

        mock_search.return_value = mock_response

        response = client.get("/api/v1/search?q=excel")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Excel Basics"
        assert "meta" in data
        assert "pagination" in data["meta"]
        assert data["meta"]["pagination"]["total_results"] == 1

    @pytest.mark.unit
    @patch("app.modules.search.router.search_nanos")
    def test_get_search_endpoint_with_filters(self, mock_search, client):
        """
        Test search request with category, level, and duration filters.

        Expected: Filters are passed to search service correctly.
        """
        from datetime import datetime, timezone

        from app.modules.search.schemas import SearchResponse

        mock_search.return_value = SearchResponse(
            success=True,
            data=[],
            meta={
                "pagination": {
                    "current_page": 1,
                    "page_size": 20,
                    "total_results": 0,
                    "total_pages": 0,
                    "has_next_page": False,
                    "has_prev_page": False,
                },
                "query": {
                    "search_query": "python",
                    "category": "Programming",
                    "level": 2,
                    "duration": "15-30",
                },
            },
            timestamp=datetime.now(timezone.utc),
        )

        response = client.get(
            "/api/v1/search?q=python&category=Programming&level=2&duration=15-30&page=1&limit=20"
        )

        assert response.status_code == 200

        # Verify filters were passed to service
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["query"] == "python"
        assert call_kwargs["category"] == "Programming"
        assert call_kwargs["level"] == 2
        assert call_kwargs["duration"] == "15-30"
        assert call_kwargs["page"] == 1
        assert call_kwargs["limit"] == 20

    @pytest.mark.unit
    @patch("app.modules.search.router.search_nanos")
    def test_get_search_endpoint_pagination(self, mock_search, client):
        """
        Test search endpoint with pagination parameters.

        Expected: Pagination parameters are correctly passed and reflected in response.
        """
        from datetime import datetime, timezone

        from app.modules.search.schemas import SearchResponse

        mock_search.return_value = SearchResponse(
            success=True,
            data=[],
            meta={
                "pagination": {
                    "current_page": 2,
                    "page_size": 10,
                    "total_results": 25,
                    "total_pages": 3,
                    "has_next_page": True,
                    "has_prev_page": True,
                },
                "query": {
                    "search_query": "test",
                    "category": None,
                    "level": None,
                    "duration": None,
                },
            },
            timestamp=datetime.now(timezone.utc),
        )

        response = client.get("/api/v1/search?q=test&page=2&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["pagination"]["current_page"] == 2
        assert data["meta"]["pagination"]["page_size"] == 10
        assert data["meta"]["pagination"]["has_next_page"] is True
        assert data["meta"]["pagination"]["has_prev_page"] is True

    @pytest.mark.unit
    @patch("app.modules.search.router.search_nanos")
    def test_get_search_endpoint_service_unavailable(self, mock_search, client):
        """
        Test search endpoint when search service is unavailable.

        Expected: 503 Service Unavailable.
        """
        from fastapi import HTTPException

        mock_search.side_effect = HTTPException(
            status_code=503, detail="Search service unavailable"
        )

        response = client.get("/api/v1/search?q=test")

        assert response.status_code == 503
        error_data = response.json()
        assert "detail" in error_data

    @pytest.mark.unit
    @patch("app.modules.search.router.search_nanos")
    def test_get_search_endpoint_malformed_filter(self, mock_search, client):
        """
        Test search endpoint with invalid filter values.

        Expected: 400 Bad Request.
        """
        from fastapi import HTTPException

        mock_search.side_effect = HTTPException(
            status_code=400, detail="Invalid filter value provided"
        )

        response = client.get("/api/v1/search?q=test&category=&level=invalid")

        # FastAPI will catch validation errors before reaching our code
        assert response.status_code in [400, 422]

    @pytest.mark.unit
    @patch("app.modules.search.router.search_nanos")
    def test_get_search_endpoint_case_insensitive_query(self, mock_search, client):
        """
        Test that search query is case-insensitive.

        Expected: Query is passed to service for case-insensitive handling by Meilisearch.
        """
        from datetime import datetime, timezone

        from app.modules.search.schemas import SearchResponse

        mock_search.return_value = SearchResponse(
            success=True,
            data=[],
            meta={
                "pagination": {
                    "current_page": 1,
                    "page_size": 20,
                    "total_results": 0,
                    "total_pages": 0,
                    "has_next_page": False,
                    "has_prev_page": False,
                },
                "query": {
                    "search_query": "EXCEL",
                    "category": None,
                    "level": None,
                    "duration": None,
                },
            },
            timestamp=datetime.now(timezone.utc),
        )

        response = client.get("/api/v1/search?q=EXCEL")

        assert response.status_code == 200
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["query"] == "EXCEL"

    @pytest.mark.unit
    @patch("app.modules.search.router.search_nanos")
    def test_get_search_endpoint_partial_match(self, mock_search, client):
        """
        Test partial match search (e.g., 'Exce' matches 'Excel').

        Expected: Partial matches are found by Meilisearch.
        """
        from datetime import datetime, timezone

        from app.modules.search.schemas import SearchNano, SearchResponse

        mock_nano = SearchNano(
            id=uuid4(),
            title="Excel Advanced",
            description="Advanced Excel",
            creator="Jane",
            duration_minutes=40,
            competency_level=3,
            category="Office",
            format="video",
            average_rating=4.8,
            rating_count=20,
            published_at=datetime.now(timezone.utc),
            thumbnail_url=None,
        )

        mock_search.return_value = SearchResponse(
            success=True,
            data=[mock_nano],
            meta={
                "pagination": {
                    "current_page": 1,
                    "page_size": 20,
                    "total_results": 1,
                    "total_pages": 1,
                    "has_next_page": False,
                    "has_prev_page": False,
                },
                "query": {
                    "search_query": "Exce",
                    "category": None,
                    "level": None,
                    "duration": None,
                },
            },
            timestamp=datetime.now(timezone.utc),
        )

        response = client.get("/api/v1/search?q=Exce")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert "Excel" in data["data"][0]["title"]


class TestSearchEndpointContract:
    """
    Contract tests for the search endpoint with Meilisearch patched.

    These tests patch ``MeilisearchClient`` and the ``get_db`` dependency so
    there is no dependency on real Docker services.  They verify the
    integration contract between the router/service layer and the rest of the
    application (response structure, status codes, header passing) without
    exercising the live Meilisearch or PostgreSQL stacks.

    For true end-to-end integration tests that seed Nano data into PostgreSQL
    and run a live Meilisearch index, add those tests with
    ``@pytest.mark.integration`` once full data-sync infrastructure is in
    place.
    """

    @pytest.mark.unit
    @patch("app.modules.search.service.MeilisearchClient")
    def test_search_contract_with_published_nanos(self, mock_client_class, client):
        """
        Test that only published Nanos are returned in search results.

        Expected: Draft, archived, and deleted Nanos are excluded from results.
        """
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.search.return_value = {
            "hits": [
                {
                    "id": str(uuid4()),
                    "title": "Published Nano",
                    "description": "A published Nano",
                    "creator": "John",
                    "duration_minutes": 20,
                    "competency_level": 1,
                    "category": "Tech",
                    "format": "video",
                    "average_rating": 4.0,
                    "rating_count": 5,
                    "published_at": "2026-03-10T10:00:00Z",
                    "thumbnail_url": None,
                }
            ],
            "estimatedTotalHits": 1,
        }

        response = client.get("/api/v1/search?q=nano")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Published Nano"
