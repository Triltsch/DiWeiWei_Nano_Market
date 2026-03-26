# DiWeiWei Nano-Marktplatz

![DiWeiWei Nano Market Logo](logo/logo.png)

Marktplatz für Nano-Lerneinheiten mit JWT-Authentifizierung, Audit-Logging und umfassenden Tests.

## 📊 Status

**Abgeschlossene Sprints:**
- ✅ Sprint 1-2: Foundation & Security, Upload, Frontend Basis
- ✅ Sprint 3: Nano Management & Landing Page
- ✅ Sprint 4: Search Infrastruktur & Discovery
- ✅ Sprint 5: Monitoring, Nano Detail, Creator Dashboard, QA/Operations Gate
- ✅ Sprint 6: Feedback-System (Ratings, Comments, Moderation, Frontend-Integration, Observability, QA-Gate)

**Aktueller Sprint:**
- 🚧 Sprint 7 (geplant): Communication (Chat Sessions, Messages, TLS-Baseline, Chat UI, QA-Gate)

Für detaillierte Feature-Liste siehe [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md).

**Qualität:** Backend-Tests ✅ | Code Coverage >70% ✅ | Frontend Vitest aktiv ✅ | Black/isort ✅

## 📌 Sprint 7 Planung

**Abschluss Sprint 6:**
- ✅ [#83](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/83) – Backend Star Rating
- ✅ [#84](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/84) – Backend Comments/Reviews
- ✅ [#85](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/85) – Moderationsworkflow
- ✅ [#86](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/86) – Frontend-Integration Rating/Comments
- ✅ [#87](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/87) – QA-Gate Feedback-System
- ✅ [#88](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/88) – Observability Feedback-Endpunkte

**Sprintziel (Sprint 7):**
Direkte Kommunikation zwischen Lernenden und Creator als Ende-zu-Ende-Flow liefern (Session, Nachrichten, Polling-UI, Transport-Security-Baseline, QA-Gate).

**Geplant für Sprint 7:**
- 🚧 [#100](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/100) – Backend Chat Session API (Story 5.1)
- 🚧 [#101](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/101) – Backend Message Persistence & Polling API (Story 5.2)
- 🚧 [#102](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/102) – Chat Transport Security Baseline (TLS + Rate Limit) (Story 5.4)
- 🚧 [#103](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/103) – Frontend Chat UI mit Polling (Story 5.3)
- 🚧 [#104](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/104) – QA-Gate Communication

**Leitlinien:**
- Search-Stack: **Meilisearch** (MVP)
- Performance DoD: **<500ms p95**
- Security/Compliance: Pflichtbestandteil Story-Abnahme

## 🚀 Quick Start

> **📚 Full setup with troubleshooting, migrations, and MinIO config:** [doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md)

**Requirements:** Python 3.13.1+, Docker & Docker Compose

**Start Backend:**
```bash
git clone https://github.com/Triltsch/DiWeiWei_Nano_Market.git && cd DiWeiWei_Nano_Market
python -m venv .venv && .\.venv\Scripts\Activate.ps1  # or source .venv/bin/activate
pip install -e .
cp .env.example .env  # configure as needed
docker-compose up -d && python scripts/init_db.py
python -m uvicorn app.main:app --reload
```
API: http://localhost:8000 | Docs: http://localhost:8000/docs

**Start Frontend:**
```bash
cd frontend && npm install && npm run dev
```
Frontend: http://localhost:5173

**Run Tests:**
```bash
pytest tests/ -v                    # Backend tests
cd frontend && npx vitest run       # Frontend tests (CI-stabil)
```

## 🐳 Docker Services

**docker-compose.yml:**
- PostgreSQL 13 (5432), Redis 7 (6379), MinIO (9000/9001)
- Meilisearch v1.6.0 (7700), FastAPI (8000)
- Prometheus (9090), Grafana (3001, admin/admin)
- Exporters: PostgreSQL (9187), Redis (9121)

```bash
docker-compose up -d           # Start all services
docker-compose ps              # Health check (all should be "healthy")
docker-compose down            # Stop services
```

**Access:**
- API: http://localhost:8000 | Swagger: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- MinIO: http://localhost:9001 (minioadmin/minioadmin)
- Meilisearch: http://localhost:7700

Runbooks: [doc/MONITORING_SETUP.md](doc/MONITORING_SETUP.md) | [doc/FEEDBACK_OBSERVABILITY_RUNBOOK.md](doc/FEEDBACK_OBSERVABILITY_RUNBOOK.md) | [doc/SPRINT5_QA_GATE.md](doc/SPRINT5_QA_GATE.md) | [doc/SPRINT6_QA_GATE.md](doc/SPRINT6_QA_GATE.md)

## 📚 API & Roles

**Full API Documentation:** http://localhost:8000/docs

### Roles & Access (MVP)
- **Rollen:** `creator` (default), `moderator`, `admin`, `consumer` (legacy read-only)
- **JWT Claim:** `role` – used in frontend routing and API guards

| Action | consumer | creator | moderator | admin |
|--------|:--------:|:-------:|:---------:|:-----:|
| Dashboard/Upload | ❌ | ✅ | ✅ | ✅ |
| Moderation Queue | ❌ | ❌ | ✅ | ✅ |
| Admin Panel | ❌ | ❌ | ❌ | ✅ |
| View Public Content | ✅ | ✅ | ✅ | ✅ |

### Authentication (Implemented)
- `POST /api/v1/auth/register` – Registration
- `POST /api/v1/auth/login` – Login (JWT Access + Refresh)
- `POST /api/v1/auth/verify-email` – Email verification
- `POST /api/v1/auth/refresh-token` – Refresh access token
- `POST /api/v1/auth/logout` – Logout

### Nanos & Upload (Implemented – Sprint 2-5)
- `POST /api/v1/upload/nano` – Upload ZIP (creates draft)
- `GET /api/v1/nanos/{nano_id}` – Fetch nano metadata
- `GET /api/v1/nanos/{nano_id}/detail` – Detail view with role-based visibility
- `GET /api/v1/nanos/my-nanos` – Creator list with status/filter
- `DELETE /api/v1/nanos/{nano_id}` – Delete/archive own nano (creator)
- `POST /api/v1/nanos/{nano_id}/metadata` – Update metadata (creator, draft only)
- `PATCH /api/v1/nanos/{nano_id}/status` – Change status (state machine)

### Search (Implemented – Sprint 4)
- `GET /api/v1/search` – Published nanos (Redis-cached, 30min TTL, deterministic keys)

### Comments (Implemented – Sprint 4+)
- `GET /api/v1/nanos/{nano_id}/comments` – Public comments (approved only)
- `POST /api/v1/nanos/{nano_id}/comments` – Add comment (auth, starts pending)
- `PATCH /api/v1/nanos/{nano_id}/comments/{id}/moderation` – Approve/hide (mod/admin)

### Ratings (Implemented – Sprint 4+)
- `GET /api/v1/nanos/{nano_id}/ratings` – Aggregation (approved only, includes own pending if auth)
- `POST /api/v1/nanos/{nano_id}/ratings` – Add 1-5 star rating (1 per user/nano, pending start)
- `PATCH /api/v1/nanos/{nano_id}/ratings/me` – Update own (resets to pending)
- `PATCH /api/v1/nanos/{nano_id}/ratings/{id}/moderation` – Approve/hide (mod/admin)

### Moderation & Audit (Implemented)
- `GET /api/v1/nanos/pending-moderation` – Queue (mod/admin)
- `GET /api/v1/audit/logs` – Audit logs (admin)
- `GET /api/v1/audit/suspicious` – Suspicious activity (admin)

### Chat (Sprint 7 – In Progress)
- `POST /api/v1/chats` – Create or reuse chat session for a nano
- `GET /api/v1/chats` – List chat sessions for current user (optional `nano_id` filter)

### Planned / In Progress (Sprint 7)
- Chat Session API ([#100](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/100))
- Chat Message Persistence + Polling API ([#101](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/101))
- Chat Transport Security Baseline ([#102](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/102))
- Frontend Chat UI mit Polling ([#103](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/103))
- QA-Gate Communication ([#104](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/104))

## 🛠️ Tech Stack

| Component | Tech | Version |
|-----------|------|---------|
| Framework | FastAPI | 0.133.1 |
| ORM | SQLAlchemy | 2.0.47 |
| Validation | Pydantic | 2.12.5 |
| Auth | JWT (python-jose) | 3.3.0 |
| Crypto | passlib + bcrypt | 1.7.4 |
| DB (Prod) | PostgreSQL | 13+ |
| DB (Test) | SQLite | – |
| Testing | pytest + Vitest | 9.0.2 / 3.x |
| Storage | MinIO | 2024-12-13 |
| Search | Meilisearch | 1.6.0 |
| Frontend | React + Vite + TypeScript + TanStack Query | 18 / 5 / 5.x |

## 📖 Documentation

### Core Guides
- [doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md) – Full setup, troubleshooting, MinIO
- [doc/DATABASE_MIGRATIONS.md](./doc/DATABASE_MIGRATIONS.md) – Alembic workflow & best practices
- Local DB recovery tip: if Alembic shows `head` but core tables are missing, use the recovery runbook in [doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md#issue-5-alembic-shows-head-but-core-tables-are-missing)
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) – Detailed feature status
- [LEARNINGS.md](./LEARNINGS.md) – Operational implementation and review ruleset

### Feature Docs
- [doc/AUDIT_LOGGING.md](./doc/AUDIT_LOGGING.md) – AuditLogger framework (40+ event types)
- [doc/FRONTEND_S2_SETUP.md](./doc/FRONTEND_S2_SETUP.md) – React/Vite/Tailwind seed
- [doc/REACT_QUERY_SETUP.md](./doc/REACT_QUERY_SETUP.md) – TanStack Query integration
- [doc/SEARCH_CACHE.md](./doc/SEARCH_CACHE.md) – Redis cache strategy (TTL, keys, invalidation, degraded mode)
- [doc/SEARCH_OPERATIONS.md](./doc/SEARCH_OPERATIONS.md) – Search API contract, pagination, performance baseline
- [doc/SPRINT6_QA_GATE.md](./doc/SPRINT6_QA_GATE.md) – QA gate evidence for feedback integration + moderation flows

## 🔒 Security

- **Password:** Bcrypt (Cost 12, OWASP)
- **Account Lockout:** 3 failed attempts → 60 min ban
- **Email:** Verification required before login (JWT, 24h)
- **Sessions:** Access Token (15 min) + Refresh (7 days)
- **Audit:** All security events logged with IP, User-Agent, timestamp

---

**Last Updated:** March 2026

