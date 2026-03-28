# DiWeiWei Nano-Marktplatz

![DiWeiWei Nano Market Logo](logo/logo.png)

Marktplatz für Nano-Lerneinheiten mit JWT-Authentifizierung, Audit-Logging und umfassenden Tests.

## 📊 Status auf einen Blick

**Abgeschlossen:** Sprint 1 bis Sprint 7  
Foundation, Upload/Storage, Search, Monitoring, Nano Detail, Creator Dashboard, Feedback-System sowie Communication (Chat, Polling, TLS-Baseline, QA-Gate).

**In Arbeit:** Sprint 8 (Profile, Moderation, Admin)  
User Profile & Account Settings, Content Review Workflow, Admin Takedown Functions und Admin Panel UI.

**Als Nächstes:** Sprint 9 (Security Hardening & CI/CD)  
CI/CD Pipeline, SSL/TLS-Hardening, Flag System und Spam Prevention.

Für den vollständigen Funktionsstand siehe [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md).

## 📌 Aktueller Sprint (Sprint 8)

**Sprintziel:**
Profil- und Admin-Funktionen Ende-zu-Ende liefern: User Self-Service, Moderationsworkflow und Admin-Oberfläche.

**Priorisierte Sprint-8-Issues:**
- 🚧 [#111](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/111) – Account Settings & DSGVO Self-Service API (Backend)
- 🚧 [#112](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/112) – Content Review Workflow & Moderation Queue API (Backend)
- 🚧 [#113](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/113) – Admin Takedown Functions with Audit Trail (Backend)
- 🚧 [#114](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/114) – User Profile & Account Settings UI (Frontend)
- 🚧 [#115](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/115) – Admin Panel UI (Frontend)
- 🚧 [#116](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/116) – QA-Gate User Profile, Moderation and Admin

**Leitplanken:**
- Search-Stack: **Meilisearch** (MVP)
- Performance-DoD: **<500ms p95**
- Security/Compliance sind Pflichtbestandteil der Story-Abnahme

## ⏭️ Nächste Schritte

- Sprint-8-Backend-Enabler und Frontend-Integration synchronisieren
- Sprint-8-QA-Gate [#116](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/116) als Abnahmekriterium durchführen
- Release-Readiness weiterhin über QA, Security und Observability absichern

## 🚀 Quick Start

> Vollständiges Setup inkl. Troubleshooting und Migrationen: [doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md)

**Requirements:** Python 3.13.1+, Docker & Docker Compose

**Backend starten:**
```bash
git clone https://github.com/Triltsch/DiWeiWei_Nano_Market.git && cd DiWeiWei_Nano_Market
python -m venv .venv && .\.venv\Scripts\Activate.ps1  # or source .venv/bin/activate
pip install -e .
cp .env.example .env  # configure as needed
docker-compose up -d && python scripts/init_db.py
python -m uvicorn app.main:app --reload
```
API: http://localhost:8000 | Docs: http://localhost:8000/docs

**Frontend starten:**
```bash
cd frontend && npm install && npm run dev
```
Frontend: http://localhost:5173

**Tests ausführen:**
```bash
pytest tests/ -v                    # Backend tests
cd frontend && npx vitest run       # Frontend tests (CI-stabil)
```

## 🐳 Docker Kurzüberblick

Lokal werden u. a. PostgreSQL, Redis, MinIO, Meilisearch, FastAPI, Prometheus und Grafana betrieben.

```bash
docker-compose up -d           # Start all services
docker-compose ps              # Health check (all should be "healthy")
docker-compose down            # Stop services
```

**Zugriffe:**
- API: http://localhost:8000 | Swagger: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- MinIO: http://localhost:9001 (minioadmin/minioadmin)
- Meilisearch: http://localhost:7700

Runbooks: [doc/MONITORING_SETUP.md](doc/MONITORING_SETUP.md) | [doc/FEEDBACK_OBSERVABILITY_RUNBOOK.md](doc/FEEDBACK_OBSERVABILITY_RUNBOOK.md) | [doc/SPRINT5_QA_GATE.md](doc/SPRINT5_QA_GATE.md) | [doc/SPRINT6_QA_GATE.md](doc/SPRINT6_QA_GATE.md)

## 👥 Rollen & Zugriff

**Rollen (MVP):** `creator` (default), `moderator`, `admin`, `consumer` (legacy read-only)  
**JWT Claim:** `role` (für API Guards und Frontend Routing)

| Action | consumer | creator | moderator | admin |
|--------|:--------:|:-------:|:---------:|:-----:|
| Dashboard/Upload | ❌ | ✅ | ✅ | ✅ |
| Moderation Queue | ❌ | ❌ | ✅ | ✅ |
| Admin Panel | ❌ | ❌ | ❌ | ✅ |
| View Public Content | ✅ | ✅ | ✅ | ✅ |

## 🔌 API Überblick

**Vollständige API-Doku:** http://localhost:8000/docs

**Authentication (implementiert):**
- `POST /api/v1/auth/register` – Registration
- `POST /api/v1/auth/login` – Login (JWT Access + Refresh)
- `POST /api/v1/auth/verify-email` – Email verification
- `POST /api/v1/auth/refresh-token` – Refresh access token
- `POST /api/v1/auth/logout` – Logout

**Nanos & Upload (implementiert):**
- `POST /api/v1/upload/nano` – Upload ZIP (creates draft)
- `GET /api/v1/nanos/{nano_id}` – Fetch nano metadata
- `GET /api/v1/nanos/{nano_id}/detail` – Detail view with role-based visibility
- `GET /api/v1/nanos/my-nanos` – Creator list with status/filter
- `DELETE /api/v1/nanos/{nano_id}` – Delete/archive own nano (creator)
- `POST /api/v1/nanos/{nano_id}/metadata` – Update metadata (creator, draft only)
- `PATCH /api/v1/nanos/{nano_id}/status` – Change status (state machine)

**Search/Feedback/Moderation (implementiert):**
- `GET /api/v1/search` – Published nanos (Redis-cached, 30min TTL, deterministic keys)
- `GET /api/v1/nanos/{nano_id}/comments` – Public comments (approved only)
- `POST /api/v1/nanos/{nano_id}/comments` – Add comment (auth, starts pending)
- `PATCH /api/v1/nanos/{nano_id}/comments/{id}/moderation` – Approve/hide (mod/admin)
- `GET /api/v1/nanos/{nano_id}/ratings` – Aggregation (approved only, includes own pending if auth)
- `POST /api/v1/nanos/{nano_id}/ratings` – Add 1-5 star rating (1 per user/nano, pending start)
- `PATCH /api/v1/nanos/{nano_id}/ratings/me` – Update own (resets to pending)
- `PATCH /api/v1/nanos/{nano_id}/ratings/{id}/moderation` – Approve/hide (mod/admin)
- `GET /api/v1/nanos/pending-moderation` – Queue (mod/admin)
- `GET /api/v1/audit/logs` – Audit logs (admin)
- `GET /api/v1/audit/suspicious` – Suspicious activity (admin)

**Chat (implementiert, Sprint 7):**
- `POST /api/v1/chats` – Create or reuse chat session for a nano
- `GET /api/v1/chats` – List chat sessions for current user (optional `nano_id` filter)

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

### Kern-Dokumente
- [doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md) – Setup, Troubleshooting, MinIO
- [doc/DATABASE_MIGRATIONS.md](./doc/DATABASE_MIGRATIONS.md) – Alembic Workflow
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) – Detaillierter Feature-Status
- [LEARNINGS.md](./LEARNINGS.md) – Operative Regeln und Best Practices

### Fachdokumente
- [doc/AUDIT_LOGGING.md](./doc/AUDIT_LOGGING.md)
- [doc/FRONTEND_S2_SETUP.md](./doc/FRONTEND_S2_SETUP.md)
- [doc/REACT_QUERY_SETUP.md](./doc/REACT_QUERY_SETUP.md)
- [doc/SEARCH_CACHE.md](./doc/SEARCH_CACHE.md)
- [doc/SEARCH_OPERATIONS.md](./doc/SEARCH_OPERATIONS.md)
- [doc/SPRINT6_QA_GATE.md](./doc/SPRINT6_QA_GATE.md)

## 🔒 Security

- **Password:** Bcrypt (Cost 12, OWASP)
- **Account Lockout:** 3 failed attempts → 60 min ban
- **Email:** Verification required before login (JWT, 24h)
- **Sessions:** Access Token (15 min) + Refresh (7 days)
- **Audit:** All security events logged with IP, User-Agent, timestamp

---

**Last Updated:** March 2026

