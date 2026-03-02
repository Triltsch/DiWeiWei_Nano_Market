# 12 — Sprint 2 Issue Plan (Week 2)

---

## 1. Sprint Goal

Enable end-to-end Nano upload baseline with persistent metadata storage and object storage, while bootstrapping the frontend stack for parallel development from Sprint 3 onward.

**Roadmap source:** [08_backlog_roadmap.md](./08_backlog_roadmap.md), Sprint 2

**In Scope (must match roadmap):**
- Story 2.1: Nano Upload with ZIP Validation (Backend)
- Story 7.2: PostgreSQL Setup & Schema Migrations
- Story 7.3: MinIO Object Storage Setup
- Story 8.1: Frontend Project Setup (React 18 + Vite + Tailwind CSS)

---

## 2. Planned Issues (Issue-Ready)

## Backend Track

### S2-BE-01 — Define Nano Upload Domain Model + Migration
- **Story:** 2.1 + 7.2
- **Type:** Feature
- **Labels:** `sprint-2`, `backend`, `database`, `story-2.1`, `story-7.2`
- **Estimate:** 1.5 PT
- **Description:** Add initial DB model(s) and Alembic migration(s) for Nano upload lifecycle (`draft` baseline) and object references.
- **Acceptance Criteria:**
  - Migration creates required upload-related schema without breaking existing auth/DSGVO data.
  - Rollback works cleanly.
  - Status field supports initial `draft` state.
  - Indexes added for expected lookup paths.
- **Dependencies:** Sprint 1 baseline merged.

### S2-BE-02 — Implement ZIP Upload API Endpoint
- **Story:** 2.1
- **Type:** Feature
- **Labels:** `sprint-2`, `backend`, `api`, `upload`, `story-2.1`
- **Estimate:** 2 PT
- **Description:** Implement authenticated endpoint to accept ZIP uploads and create draft Nano records.
- **Acceptance Criteria:**
  - ZIP-only input accepted; other formats rejected with clear error.
  - Max upload size = 100 MB enforced.
  - Successful upload creates Nano record with status `draft`.
  - Response payload includes upload/nano identifier for next metadata step.
- **Dependencies:** `S2-BE-01`.

### S2-BE-03 — Add ZIP Structure Validation Service
- **Story:** 2.1
- **Type:** Feature
- **Labels:** `sprint-2`, `backend`, `validation`, `upload`, `story-2.1`
- **Estimate:** 1.5 PT
- **Description:** Validate ZIP internal structure and ensure at least one supported content file exists.
- **Acceptance Criteria:**
  - Corrupt ZIP files are rejected.
  - Empty ZIP files are rejected.
  - ZIP with at least one supported file type is accepted.
  - Validation errors are user-friendly and API-consistent.
- **Dependencies:** `S2-BE-02`.

### S2-BE-04 — Integrate MinIO Storage Adapter
- **Story:** 7.3 + 2.1
- **Type:** Feature
- **Labels:** `sprint-2`, `backend`, `infrastructure`, `minio`, `story-7.3`, `story-2.1`
- **Estimate:** 2 PT
- **Description:** Implement object storage adapter for upload persistence in MinIO (private ACL), with deterministic key naming.
- **Acceptance Criteria:**
  - Uploads stored in MinIO bucket using private access policy.
  - Metadata links object key to Nano draft record.
  - Storage failures return recoverable API errors.
  - Local Compose environment works with configured MinIO service.
- **Dependencies:** `S2-BE-02`, `S2-OPS-01`.

### S2-BE-05 — Upload Retry + Timeout Handling
- **Story:** 2.1
- **Type:** Enhancement
- **Labels:** `sprint-2`, `backend`, `resilience`, `story-2.1`
- **Estimate:** 1 PT
- **Description:** Add timeout guardrails and retry semantics for failed uploads.
- **Acceptance Criteria:**
  - Timeout limit set to 10 minutes for upload operation.
  - Retry path available for transient failures.
  - Failure state is visible in API response contract.
- **Dependencies:** `S2-BE-04`.

### S2-BE-06 — Backend Tests for Upload + Storage Flow
- **Story:** 2.1 + 7.2 + 7.3
- **Type:** Test
- **Labels:** `sprint-2`, `backend`, `tests`, `story-2.1`, `story-7.2`, `story-7.3`
- **Estimate:** 2 PT
- **Description:** Add/extend unit + integration tests for upload endpoint, ZIP validation, DB write path, and MinIO integration (mock + optional real).
- **Acceptance Criteria:**
  - Upload handler tests pass.
  - ZIP validation edge cases are covered.
  - DB persistence assertions included.
  - MinIO integration tests available with CI-safe mode.
- **Dependencies:** `S2-BE-01`..`S2-BE-05`.

## Infrastructure / DevOps Track

### S2-OPS-01 — Provision PostgreSQL + MinIO in Compose
- **Story:** 7.2 + 7.3
- **Type:** Infrastructure
- **Labels:** `sprint-2`, `devops`, `docker-compose`, `postgresql`, `minio`, `story-7.2`, `story-7.3`
- **Estimate:** 1.5 PT
- **Description:** Ensure local environment includes stable PostgreSQL and MinIO services with persistent volumes and health checks.
- **Acceptance Criteria:**
  - `docker-compose` starts services successfully.
  - Health checks pass for DB and MinIO.
  - Credentials and endpoints sourced from environment config.
  - Persistent volumes survive restart.
- **Dependencies:** none.

### S2-OPS-02 — Migration Workflow + Developer Setup Docs
- **Story:** 7.2
- **Type:** Documentation / DevEx
- **Labels:** `sprint-2`, `devops`, `database`, `docs`, `story-7.2`
- **Estimate:** 1 PT
- **Description:** Document migration commands, local setup sequence, and troubleshooting for Sprint 2 components.
- **Acceptance Criteria:**
  - Developer onboarding covers DB + MinIO + upload prerequisites.
  - Migration apply/rollback steps documented.
  - Common setup failures and fixes documented.
- **Dependencies:** `S2-OPS-01`, `S2-BE-01`.

## Frontend Track

### S2-FE-01 — Bootstrap React 18 + Vite + TypeScript App
- **Story:** 8.1
- **Type:** Feature
- **Labels:** `sprint-2`, `frontend`, `bootstrap`, `story-8.1`
- **Estimate:** 1 PT
- **Description:** Initialize frontend workspace with React 18, Vite, and strict TypeScript baseline.
- **Acceptance Criteria:**
  - App builds and runs via `npm run dev`.
  - TypeScript strict mode active.
  - Project structure ready for feature modules.
- **Dependencies:** none.

### S2-FE-02 — Configure Tailwind + Design Tokens
- **Story:** 8.1
- **Type:** Feature
- **Labels:** `sprint-2`, `frontend`, `tailwind`, `design-system`, `story-8.1`
- **Estimate:** 1 PT
- **Description:** Add Tailwind CSS setup and initial design token mapping per architecture guidelines.
- **Acceptance Criteria:**
  - Tailwind configured and active in app.
  - Shared token definitions created for colors/typography.
  - Baseline style entrypoint committed.
- **Dependencies:** `S2-FE-01`.

### S2-FE-03 — Add Router Skeleton + Base Routes
- **Story:** 8.1
- **Type:** Feature
- **Labels:** `sprint-2`, `frontend`, `routing`, `story-8.1`
- **Estimate:** 1 PT
- **Description:** Add React Router v6 setup with placeholder pages for planned MVP routes.
- **Acceptance Criteria:**
  - Routes exist: `/`, `/search`, `/nano/:id`, `/login`, `/register`, `/dashboard`, `/profile`, `/admin`.
  - Unknown routes handled with fallback.
  - Routing structure supports protected routes in Sprint 3.
- **Dependencies:** `S2-FE-01`.

### S2-FE-04 — Configure Axios Client + JWT Injection Hook Points
- **Story:** 8.1
- **Type:** Feature
- **Labels:** `sprint-2`, `frontend`, `api-client`, `auth`, `story-8.1`
- **Estimate:** 1 PT
- **Description:** Add centralized Axios client configured from environment and prepared for token injection.
- **Acceptance Criteria:**
  - Base URL loaded from environment.
  - Request interceptor supports access-token injection.
  - Error handling path prepared for auth refresh in Sprint 3.
- **Dependencies:** `S2-FE-01`.

### S2-FE-05 — Configure React Query + App Providers
- **Story:** 8.1
- **Type:** Feature
- **Labels:** `sprint-2`, `frontend`, `react-query`, `story-8.1`
- **Estimate:** 1 PT
- **Description:** Introduce React Query client/provider and shared app provider composition.
- **Acceptance Criteria:**
  - Query client configured with sane defaults.
  - Provider wiring active in app root.
  - One sample query path included for smoke validation.
- **Dependencies:** `S2-FE-01`, `S2-FE-04`.

### S2-FE-06 — Frontend Quality Tooling + Compose Integration
- **Story:** 8.1
- **Type:** Infrastructure
- **Labels:** `sprint-2`, `frontend`, `quality`, `docker`, `story-8.1`
- **Estimate:** 1.5 PT
- **Description:** Configure ESLint/Prettier, local proxy to backend `:8000`, and Docker Compose service for static serve.
- **Acceptance Criteria:**
  - Lint + formatting scripts available and passing.
  - Dev proxy forwards API requests to backend.
  - Compose service exists for frontend static artifact serving.
  - `npm run build` produces deployable bundle.
- **Dependencies:** `S2-FE-01`..`S2-FE-05`, `S2-OPS-01`.

---

## 3. Sprint 2 Delivery Order

1. `S2-OPS-01` (environment baseline)
2. `S2-BE-01` → `S2-BE-02` → `S2-BE-03` → `S2-BE-04` → `S2-BE-05`
3. `S2-BE-06` (test hardening)
4. `S2-FE-01` parallel start, then `S2-FE-02`..`S2-FE-06`
5. `S2-OPS-02` finalized after implementation details stabilize

---

## 4. Sprint 2 Definition of Done (Issue-Level)

Apply this checklist to every Sprint 2 issue before closing:

- [ ] Scope maps to one of Stories 2.1 / 7.2 / 7.3 / 8.1
- [ ] Code reviewed (PR approved)
- [ ] Unit/integration tests added or updated
- [ ] Relevant API/docs/config updated
- [ ] Security constraints respected (private object access, no secrets in code)
- [ ] CI checks green (format, lint, tests)

---

## 5. Capacity Snapshot (Planning Aid)

- **Backend + Ops:** ~9.5 PT
- **Frontend:** ~6.5 PT
- **Total Sprint 2 planned:** ~16 PT

If single-team capacity is below 16 PT, defer in this order:
1. `S2-BE-05` (retry/timeouts refinement)
2. `S2-OPS-02` (docs hardening)
3. Non-critical polish inside `S2-FE-06`

---

## Referenzen

- [08 — Backlog & Roadmap](./08_backlog_roadmap.md)
- [05 — System Architecture](./05_system_architecture.md)
- [07 — Modules](./07_modules.md)
- [09 — Testing & Quality](./09_testing_quality.md)