# DiWeiWei Nano-Marktplatz

![DiWeiWei Nano Market Logo](logo/logo.png)

Marktplatz für Nano-Lerneinheiten mit JWT-Authentifizierung, Audit-Logging und umfassenden Tests.

## 📊 Aktueller Status

- **Abgeschlossen:** Sprint 1 bis Sprint 8a
	- Sprint 8 abgeschlossen: Issues [#111](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/111), [#112](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/112), [#113](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/113), [#114](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/114), [#115](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/115), [#116](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/116)
	- Sprint 8a abgeschlossen: Issues [#125](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/125), [#126](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/126), [#127](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/127), [#128](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/128), [#129](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/129), [#130](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/130)
- **Geplant:** Sprint 9 (Security Hardening & CI/CD)
	- Offen: [#141](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/141), [#142](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/142), [#143](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/143), [#144](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/144)

Vollständiger Umsetzungsstand: [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)

## 📌 Nächster Sprint (Sprint 9, geplant)

**Sprintziel:** Produktionsreife absichern mit CI/CD, TLS-Hardening sowie Trust-&-Safety-Enablern.

**Priorisierte Issues:**
- [#144](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/144) - Implement CI/CD Pipeline with GitHub Actions
- [#142](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/142) - SSL/TLS Hardening & Reverse Proxy Configuration
- [#141](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/141) - User Reporting / Flag System for Nanos
- [#143](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/143) - Spam Prevention & Rate Limiting

**Sprint-Leitplanken:** Meilisearch (MVP), Performance-DoD <500ms p95, Security/Compliance als Pflichtbestandteil.

## ⏭️ Nächste Schritte

- Sprint-9-Issues priorisiert in Umsetzung überführen (Reihenfolge: [#144](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/144) -> [#142](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/142) -> [#141](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/141) -> [#143](https://github.com/Triltsch/DiWeiWei_Nano_Market/issues/143))
- CI-/Security-QA-Kriterien für Sprint 9 früh als Definition of Done verankern
- Sprint-10-Vorbereitung (Final QA & Go-Live) parallel in Runbooks vorstrukturieren

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

Hinweis für Verifikationsmails:
- In Staging/Produktion `PUBLIC_BASE_URL` auf die extern erreichbare URL setzen (z. B. `https://nano.example.com`).
- `localhost`-Links sind nur für Development/Test gedacht.

**Tests (lokal):**
```bash
pytest tests/ -v
cd frontend && npx vitest run
```

## 🐳 Docker

Lokal laufen u. a. PostgreSQL, Redis, MinIO, Meilisearch, FastAPI, Prometheus und Grafana.

```bash
docker-compose up -d
docker-compose ps
docker-compose down
```

**Zugriffe:**
- API: http://localhost:8000 | Swagger: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- MinIO: http://localhost:9001 (minioadmin/minioadmin)
- Meilisearch: http://localhost:7700

Runbooks: [doc/MONITORING_SETUP.md](doc/MONITORING_SETUP.md) | [doc/FEEDBACK_OBSERVABILITY_RUNBOOK.md](doc/FEEDBACK_OBSERVABILITY_RUNBOOK.md) | [doc/SPRINT5_QA_GATE.md](doc/SPRINT5_QA_GATE.md) | [doc/SPRINT6_QA_GATE.md](doc/SPRINT6_QA_GATE.md) | [doc/SPRINT8_QA_GATE.md](doc/SPRINT8_QA_GATE.md)

## 👥 Rollen & Zugriff

**Rollen (MVP):** `creator` (default), `moderator`, `admin`, `consumer` (legacy read-only)  
**JWT Claim:** `role` (für API Guards und Frontend Routing)

| Action | consumer | creator | moderator | admin |
|--------|:--------:|:-------:|:---------:|:-----:|
| Dashboard/Upload | ❌ | ✅ | ✅ | ✅ |
| Moderation Queue | ❌ | ❌ | ✅ | ✅ |
| Admin Panel | ❌ | ❌ | ❌ | ✅ |
| View Public Content | ✅ | ✅ | ✅ | ✅ |

## 🔌 API Überblick (kompakt)

Vollständige API-Doku: http://localhost:8000/docs

Implementierte Kernbereiche:
- Auth (Register, Login, Verify, Refresh, Logout)
- Nano Upload & Management (Draft-Workflow, Metadata, Status-Transitions)
- Search (Meilisearch + Redis Cache)
- Feedback & Moderation (Kommentare, Ratings, Moderationsqueue)
- Chat (Session erstellen/wiederverwenden, Sessions listen)
- Audit (Logs, suspicious activity)

## 🛠️ Tech Stack

| Component | Tech | Version |
|-----------|------|---------|
| Framework | FastAPI | 0.133.1 |
| Auth | JWT (python-jose) | 3.3.0 |
| Crypto | passlib + bcrypt | 1.7.4 |
| Database | PostgreSQL (Prod), SQLite (Test) | 13+ / - |
| Validation/ORM | Pydantic + SQLAlchemy | 2.12.5 / 2.0.47 |
| Testing | pytest + Vitest | 9.0.2 / 3.x |
| Storage | MinIO | 2024-12-13 |
| Search | Meilisearch | 1.6.0 |
| Frontend | React + Vite + TypeScript + TanStack Query | 18 / 5 / 5.x |

## 📖 Documentation

### Kern-Dokumente
- [doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md) – Setup, Troubleshooting, MinIO
- [doc/DATABASE_MIGRATIONS.md](./doc/DATABASE_MIGRATIONS.md) – Alembic Workflow
- [doc/SSL_TLS_SETUP.md](./doc/SSL_TLS_SETUP.md) – TLS proxy setup, cert generation, verification
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) – Detaillierter Feature-Status
- [LEARNINGS.md](./LEARNINGS.md) – Operative Regeln und Best Practices

### Fachdokumente
- [doc/AUDIT_LOGGING.md](./doc/AUDIT_LOGGING.md)
- [doc/FRONTEND_S2_SETUP.md](./doc/FRONTEND_S2_SETUP.md)
- [doc/REACT_QUERY_SETUP.md](./doc/REACT_QUERY_SETUP.md)
- [doc/SEARCH_CACHE.md](./doc/SEARCH_CACHE.md)
- [doc/SEARCH_OPERATIONS.md](./doc/SEARCH_OPERATIONS.md)
- [doc/SPRINT5_QA_GATE.md](./doc/SPRINT5_QA_GATE.md)
- [doc/SPRINT6_QA_GATE.md](./doc/SPRINT6_QA_GATE.md)
- [doc/SPRINT8_QA_GATE.md](./doc/SPRINT8_QA_GATE.md)

## 🔒 Security

- **Password:** Bcrypt (Cost 12, OWASP)
- **Account Lockout:** 3 failed attempts → 60 min ban
- **Email:** Verification required before login (JWT, 24h)
- **Sessions:** Access Token (15 min) + Refresh (7 days)
- **Audit:** All security events logged with IP, User-Agent, timestamp

---

**Last Updated:** April 2026

