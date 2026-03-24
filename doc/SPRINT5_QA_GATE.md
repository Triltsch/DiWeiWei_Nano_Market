# Sprint 5 QA/Operations Gate (Issue #74)

## Scope

This gate consolidates Sprint-5 acceptance across:
- Story 7.5 (Monitoring baseline)
- Story 2.5 (Nano Detail backend)
- Story 8.5 (Nano Detail frontend)
- Story 8.6 (Creator Dashboard)

It documents integration evidence, NFR/security checks, DoD completion, and follow-ups for Sprint 6.

## Integration Validation

### End-to-end path: Search -> Detail -> Auth-Gating -> Creator Dashboard

- Discovery -> Detail -> Auth-Gating is covered in frontend routing tests:
  - `frontend/src/features/routing/pages.test.tsx`
  - scenario: `supports Discovery -> Detail -> Auth-Gating flow`
- Auth gate for protected dashboard route is covered in:
  - `frontend/src/features/routing/ProtectedRouteLayout.test.tsx`
  - scenarios: authenticated access, unauthenticated redirect, role-based forbidden
- Creator dashboard API surface and route behavior are covered in backend tests:
  - `tests/modules/nanos/test_nanos_routes.py`
  - suite: `GET /api/v1/nanos/my-nanos` route behavior and ownership constraints

Status: **validated via automated tests**.

## NFR and Operational Verification

### Latency and reliability baseline

- Search p95 latency target `<500ms` is asserted in:
  - `tests/modules/search/test_search_integration.py::test_search_latency_p95_under_500ms`
- Password hashing performance baseline remains covered in:
  - `tests/modules/auth/test_password_hashing.py`

### Monitoring visibility and alerting

- Monitoring stack and provisioning are documented in:
  - `doc/MONITORING_SETUP.md`
- Prometheus rules include baseline alerts:
  - `HighErrorRate`
  - `SlowAPI`

### Environment validation run (local)

Executed during this gate implementation:
- `docker compose pull` -> all pinned images available
- `docker compose up -d --remove-orphans` -> all required services healthy
- Prometheus targets -> `up`
- Prometheus rule groups -> present (`PROM_RULE_GROUPS=1`)
- App health endpoint -> `status=ok`
- `docker compose down` executed after validation

No blocking environment integrity issues were detected for:
- credential alignment across compose services
- port mapping consistency
- volume naming compatibility
- image tag availability

## Critical Error Scenario Matrix (401/403/404/5xx)

Validated and documented by automated tests:

- `401 Unauthorized`
  - Nano detail/download access without JWT
  - covered in `tests/modules/nanos/test_nanos_routes.py`
  - frontend typed API error mapping covered in `frontend/src/shared/api/nanoDetail.test.ts`
- `403 Forbidden`
  - restricted non-published access for unauthorized authenticated users
  - covered in `tests/modules/nanos/test_nanos_routes.py`
  - frontend typed API error mapping covered in `frontend/src/shared/api/nanoDetail.test.ts`
- `404 Not Found`
  - missing nano resources
  - covered in `tests/modules/nanos/test_nanos_routes.py`
  - frontend typed API error mapping covered in `frontend/src/shared/api/nanoDetail.test.ts`
- `5xx` (operational failure path)
  - storage presign failure -> `503`
  - covered in `tests/modules/nanos/test_nanos_routes.py`
  - frontend typed API error mapping (`request-failed`) covered in `frontend/src/shared/api/nanoDetail.test.ts`

## Sprint-5 DoD Checklist

- [x] End-to-end path `Search -> Detail -> Auth-Gating -> Creator Dashboard` validated
- [x] Monitoring shows actionable metrics/alerts for new flows
- [x] Critical scenarios `401/403/404/5xx` tested and documented
- [x] Sprint-5 DoD checklist completed
- [x] Open risks/follow-ups for Sprint 6 captured
- [x] Exactly one `Test: Verified` automation task is defined and tracked in version-controlled project tooling

## Open Risks / Follow-ups (Sprint 6)

- Add browser-level E2E (Playwright/Cypress) that covers full login continuation into creator dashboard after auth redirect from detail page.
- Add explicit endpoint-level latency assertions for nano detail and creator dashboard APIs (not only search latency baseline).
- Expand alerting from baseline to flow-specific SLO alerts (detail/download failure ratio, dashboard API error budget).
- Add periodic chaos/degraded-mode checks for Redis/MinIO to continuously validate operational fallback behavior.
