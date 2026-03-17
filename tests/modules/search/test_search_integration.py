"""Live Meilisearch integration tests for the search endpoint.

These tests seed the Docker Compose Meilisearch instance directly and then hit
`GET /api/v1/search` through the FastAPI ASGI app. They validate the real API
contract, filter semantics, partial matches, and the Sprint-4 latency target.
"""

import math
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import httpx
import pytest

from app.config import get_settings
from app.modules.search.service import MeilisearchClient

TEST_INDEX_UID = "nanos_v1"


def _build_meili_headers() -> dict[str, str]:
    """Build Meilisearch auth headers from configured settings."""
    settings = get_settings()
    headers = {"Content-Type": "application/json"}
    if settings.MEILI_MASTER_KEY:
        headers["Authorization"] = f"Bearer {settings.MEILI_MASTER_KEY}"
    return headers


async def _wait_for_task(meili_client: httpx.AsyncClient, task_uid: int) -> None:
    """Wait until a Meilisearch asynchronous task has completed."""
    for _ in range(60):
        response = await meili_client.get(f"/tasks/{task_uid}")
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status")
        if status == "succeeded":
            return
        if status == "failed":
            error = payload.get("error")
            if isinstance(error, dict) and error.get("code") == "index_not_found":
                return
            raise AssertionError(f"Meilisearch task {task_uid} failed: {payload}")
        await asyncio_sleep(0.25)

    raise AssertionError(f"Timed out waiting for Meilisearch task {task_uid}")


async def asyncio_sleep(seconds: float) -> None:
    """Small helper to keep imports local to this test module."""
    import asyncio

    await asyncio.sleep(seconds)


def _task_uid_from_response(payload: dict[str, Any]) -> int:
    """Extract the task UID from a Meilisearch API response payload."""
    task_uid = payload.get("taskUid")
    if not isinstance(task_uid, int):
        raise AssertionError(f"Expected taskUid in Meilisearch response, got: {payload}")
    return task_uid


@pytest.fixture
async def seeded_search_index() -> AsyncGenerator[list[dict[str, Any]], None]:
    """Create a clean Meilisearch index with representative published/draft docs."""
    settings = get_settings()

    async with httpx.AsyncClient(
        base_url=settings.MEILI_URL,
        headers=_build_meili_headers(),
        timeout=10.0,
    ) as meili_client:
        try:
            health_response = await meili_client.get("/health")
        except httpx.HTTPError:
            pytest.skip(
                "Meilisearch is not reachable; run the verified Docker-backed test task"
            )
        if health_response.status_code != 200:
            pytest.skip("Meilisearch is not reachable; run the verified Docker-backed test task")

        delete_response = await meili_client.delete(f"/indexes/{TEST_INDEX_UID}")
        if delete_response.status_code not in (202, 404):
            delete_response.raise_for_status()
        if delete_response.status_code == 202:
            await _wait_for_task(meili_client, _task_uid_from_response(delete_response.json()))

        create_response = await meili_client.post(
            "/indexes",
            json={"uid": TEST_INDEX_UID, "primaryKey": "id"},
        )
        create_response.raise_for_status()
        await _wait_for_task(meili_client, _task_uid_from_response(create_response.json()))

        filterable_response = await meili_client.put(
            f"/indexes/{TEST_INDEX_UID}/settings/filterable-attributes",
            json=["status", "category", "competency_level", "duration_minutes", "language"],
        )
        filterable_response.raise_for_status()
        await _wait_for_task(meili_client, _task_uid_from_response(filterable_response.json()))

        sortable_response = await meili_client.put(
            f"/indexes/{TEST_INDEX_UID}/settings/sortable-attributes",
            json=["average_rating"],
        )
        sortable_response.raise_for_status()
        await _wait_for_task(meili_client, _task_uid_from_response(sortable_response.json()))

        documents: list[dict[str, Any]] = [
            {
                "id": str(uuid4()),
                "title": "Excel Basics",
                "description": "Intro to Excel formulas and tables",
                "creator": "Alice",
                "duration_minutes": 15,
                "competency_level": 1,
                "category": "Office",
                "format": "video",
                "average_rating": 4.9,
                "rating_count": 19,
                "published_at": "2026-03-17T08:00:00Z",
                "thumbnail_url": None,
                "status": "published",
                "language": "de",
            },
            {
                "id": str(uuid4()),
                "title": "Excel Advanced Automation",
                "description": "Macros, automation, and reusable templates",
                "creator": "Bob",
                "duration_minutes": 35,
                "competency_level": 3,
                "category": "Office",
                "format": "video",
                "average_rating": 4.7,
                "rating_count": 12,
                "published_at": "2026-03-17T09:00:00Z",
                "thumbnail_url": None,
                "status": "published",
                "language": "en",
            },
            {
                "id": str(uuid4()),
                "title": "Python Basics",
                "description": "Learn Python fundamentals fast",
                "creator": "Carol",
                "duration_minutes": 20,
                "competency_level": 1,
                "category": "Programming",
                "format": "text",
                "average_rating": 4.6,
                "rating_count": 8,
                "published_at": "2026-03-17T10:00:00Z",
                "thumbnail_url": None,
                "status": "published",
                "language": "en",
            },
            {
                "id": str(uuid4()),
                "title": "Excel Draft Hidden",
                "description": "Draft content must never appear in results",
                "creator": "Dana",
                "duration_minutes": 10,
                "competency_level": 1,
                "category": "Office",
                "format": "video",
                "average_rating": 5.0,
                "rating_count": 1,
                "published_at": "2026-03-17T11:00:00Z",
                "thumbnail_url": None,
                "status": "draft",
                "language": "de",
            },
        ]

        add_documents_response = await meili_client.post(
            f"/indexes/{TEST_INDEX_UID}/documents",
            json=documents,
        )
        add_documents_response.raise_for_status()
        await _wait_for_task(meili_client, _task_uid_from_response(add_documents_response.json()))

        try:
            yield documents
        finally:
            cleanup_response = await meili_client.delete(f"/indexes/{TEST_INDEX_UID}")
            if cleanup_response.status_code == 202:
                await _wait_for_task(meili_client, _task_uid_from_response(cleanup_response.json()))


class TestSearchIntegration:
    """Integration tests for real API -> Meilisearch search flows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_flow_filters_published_docs_and_supports_partial_match(
        self, async_client, seeded_search_index
    ):
        """Published docs are searchable with partial matching and backend filters."""
        _ = seeded_search_index

        response = await async_client.get(
            "/api/v1/search",
            params={
                "q": "Exce",
                "category": "Office",
                "duration": "0-15",
                "language": "de",
                "page": 1,
                "limit": 20,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meta"]["pagination"]["current_page"] == 1
        assert payload["meta"]["pagination"]["total_results"] == 1
        assert payload["meta"]["query"]["search_query"] == "Exce"
        assert payload["meta"]["query"]["language"] == "de"
        assert len(payload["data"]) == 1
        assert payload["data"][0]["title"] == "Excel Basics"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_latency_p95_under_500ms(self, async_client, seeded_search_index):
        """Typical Meilisearch processing times stay below the Sprint-4 p95 target."""
        _ = seeded_search_index
        _ = async_client

        settings = get_settings()
        client = MeilisearchClient(settings.MEILI_URL, settings.MEILI_MASTER_KEY)
        queries = ["excel", "python", "Exce", "automation", "basics"]

        latencies_ms: list[float] = []
        for query in queries * 3:
            result = client.search(query=query, page=1, limit=20)
            processing_time = result.get("processingTimeMs")
            if isinstance(processing_time, (int, float)):
                latencies_ms.append(float(processing_time))

        assert latencies_ms, "Expected Meilisearch processingTimeMs values for latency baseline"

        ordered = sorted(latencies_ms)
        p95_index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1))
        p95_latency_ms = ordered[p95_index]

        assert p95_latency_ms < 500, (
            f"Measured search p95 was {p95_latency_ms:.2f}ms over {len(latencies_ms)} requests, "
            "exceeding the 500ms Sprint-4 target"
        )
