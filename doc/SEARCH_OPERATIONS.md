# Search Operations & QA Gate (Issue #63)

## Scope
This document captures the Sprint-4 operating contract for the Meilisearch-based discovery flow across backend, frontend, and infrastructure.

## API Contract
`GET /api/v1/search`

### Query Parameters
- `q` (required): case-insensitive full-text query
- `category` (optional): exact category filter
- `level` (optional): competency level `1`, `2`, or `3`
- `duration` (optional): `0-15`, `15-30`, or `30+`
- `language` (optional): ISO 639-1 content language, e.g. `de`, `en`
- `page` (optional): 1-based page number, default `1`
- `limit` (optional): page size, default `20`, max `100`

### Response Contract
The endpoint returns the unified API envelope:
- `success`
- `data`
- `meta.pagination`
- `meta.query`
- `timestamp`

The frontend discovery client maps `meta.pagination` to its load-more UI state. Legacy offset-based callers are normalized to the backend page contract before the request is sent.

## Filters & Pagination Semantics
- Search only returns Nanos with `status = published`
- Filters combine with logical `AND`
- Partial matches are handled by Meilisearch
- Pagination is page-based in the API and translated to the discovery UI load-more interaction
- Redis cache keys are parameter-complete and include `q`, `category`, `level`, `duration`, `language`, `page`, and `limit`

## Performance Baseline
The automated integration test suite validates the Sprint-4 latency target with the live Docker Compose Meilisearch service:
- test: `tests/modules/search/test_search_integration.py::test_search_latency_p95_under_500ms`
- target: p95 typical query latency `< 500ms`
- execution path: API -> Meilisearch index with representative seeded documents

## Security Minimum Checks
The search endpoint enforces and/or documents the following minimum checks:
- Input validation on `q`, `level`, `duration`, `language`, `page`, and `limit`
- Filter escaping for string filters before Meilisearch filter expression generation
- Published-only constraint to prevent draft leakage
- Pagination upper bound (`limit <= 100`) to reduce abusive fan-out queries
- Redis degraded mode fallback so cache outages do not break search availability
- Cache observability uses hashed key fingerprints instead of raw user queries in logs
- Health endpoint reports Redis degradation explicitly (`status: degraded`)
- CORS remains origin-scoped when credentials are enabled

## Test Coverage Overview
- Backend unit tests: query validation, cache key completeness, cache degraded mode, route contract
- Backend integration tests: real Meilisearch partial-match/filter flow and latency baseline
- Frontend contract tests: backend envelope mapping and page-based request normalization
- Frontend page tests: URL sync, filter state, empty state, and load-more pagination behavior

## Sprint-4 DoD Checklist
- [x] Search backend and frontend use the same request/response contract
- [x] p95 search latency is asserted below 500ms in automated integration coverage
- [x] Backend unit/integration tests for search are green
- [x] Frontend discovery contract/page tests cover search integration behavior
- [x] Search cache/filter/pagination/security behavior is documented
- [x] `Test: Verified` remains uniquely defined in `.vscode/tasks.json`
