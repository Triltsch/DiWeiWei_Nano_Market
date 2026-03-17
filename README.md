# DiWeiWei Nano-Marktplatz

![DiWeiWei Nano Market Logo](logo/logo.png)

Marktplatz für Nano-Lerneinheiten mit JWT-Authentifizierung, Audit-Logging und umfassenden Tests.

## 📊 Aktueller Stand

**Fertiggestellte Stories**: 1.1, 1.3, 1.4, 1.5, 7.2, 7.3, 8.1, 8.2, 8.4, 2.2, 2.4, 7.4 ✅
- ✅ User Registration & Login mit Email-Verifizierung
- ✅ Password Hashing (Bcrypt, OWASP-konform)
- ✅ Email Verification Flow (JWT-basiert)
- ✅ Audit Logging Framework (40+ Event-Typen)
- ✅ ZIP Upload API (Nano-Lerneinheiten hochladen)
- ✅ Nano Upload Domain Model mit Alembic Migrations
- ✅ Frontend Foundation (React 18 + Vite + Tailwind + Router)
- ✅ Zentraler Axios HTTP-Client mit JWT-Injection (S2-FE-04)
- ✅ React Query + App Provider Composition inkl. Sample Query Hook (S2-FE-05)
- ✅ Nano Metadata Capture (Story 2.2) - GET/POST metadata endpoints with validation
- ✅ Nano Status Workflow (Story 2.4) - PATCH endpoint for status transitions with state machine validation
- ✅ Landing Page & Global Navigation (Story 8.2) - Responsive navbar with hamburger menu, active route highlighting, language selector placeholder, WCAG 2.1 AA compliance
- ✅ Nano Discovery Page & Search UI (Story 8.4) - `/search` with debounce, filters, loading/empty states, URL sync, and load-more pagination
- ✅ Redis Cache Setup für Search (Story 7.4) - deterministische Cache-Keys, 30-Minuten TTL, Invalidierung bei Nano-Datenänderungen, degraded mode ohne API-Ausfall

**Qualität**:
- 266/266 Tests bestanden (100%)
- Code Coverage erfolgreich (Ziel: >70%)
- Frontend: Vitest Test-Setup aktiv (`npm test`)
- Black/isort Code-Formatierung
- PostgreSQL + SQLite Support

## 🚀 Quick Start

> **📚 For comprehensive setup instructions**, including troubleshooting, migration workflows, and MinIO configuration, see **[doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md)**.

### Voraussetzungen
- Python 3.13.1+
- Docker & Docker Compose (für lokale Services)

### Installation & Start

```bash
# 1. Repository klonen
git clone https://github.com/Triltsch/DiWeiWei_Nano_Market.git
cd DiWeiWei_Nano_Market

# 2. Virtual Environment erstellen und aktivieren
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate    # macOS/Linux

# 3. Dependencies installieren
pip install -e .

# 4. Umgebungsvariablen konfigurieren
cp .env.example .env
# .env editieren und SECRET_KEY, DATABASE_URL etc. anpassen

# 5. Docker Services starten (PostgreSQL, Redis, MinIO, Meilisearch)
docker-compose up -d

# 6. Datenbank initialisieren
python scripts/init_db.py

# 7. Anwendung starten
python -m uvicorn app.main:app --reload
```

**API Dokumentation**: http://localhost:8000/docs

### Frontend starten (Story 8.1)

```bash
# Frontend Workspace wechseln
cd frontend

# Dependencies installieren
npm install

# Dev Server starten (Vite)
npm run dev

# Optional: Typprüfung und Frontend-Tests
npm run typecheck
npm test
```

Frontend Dev Server: http://localhost:5173

### Tests ausführen

```bash
# Standard: CI-safe Tests (SQLite/PostgreSQL + gemocktes MinIO)
pytest tests/ -v

# Mit Coverage Report
pytest tests/ --cov=app --cov-report=html

# Optional: echte MinIO-Integrationstests aktivieren
# (setzt laufendes MinIO via docker-compose voraus)
RUN_REAL_MINIO_TESTS=1 pytest tests/modules/upload/test_storage.py -k real_minio -v

# Frontend Tests (Vitest)
cd frontend
npm test

# Frontend Build + Typecheck
npm run typecheck
npm run build
```

## 📋 Implementierte Features

### Sprint 1 – Foundation & Security
- **Story 1.1 / Issue #2 – User Registration & Login**
  - Registrierung mit eindeutiger E-Mail, Username-Regeln und Passwortvalidierung
  - E-Mail-Verifizierung mit 24h Token-Laufzeit und Resend-Flow
  - Login mit JWT Access Token (15 Min.) und Refresh Token (7 Tage)
  - Account-Lockout nach mehrfachen Fehlversuchen sowie Logout-/Session-Handling
- **Story 1.3 / Issue #4 – Password Hashing Implementation**
  - Sichere Passwort-Hashing- und Verify-Logik auf Basis von bcrypt
  - Durchsetzung der Passwort-Policy inkl. Stärkevalidierung
  - Keine Speicherung oder Protokollierung von Klartext-Passwörtern
- **Story 1.4 / Issue #5 – DSGVO Compliance Basics**
  - Consent-Tracking für Nutzungsbedingungen und Datenschutz
  - Datenexport im maschinenlesbaren Format
  - Löschanforderungen mit Grace-Period sowie Privacy-/ToS-Verknüpfung im Flow
- **Story 1.5 / Issue #6 – Audit Logging Framework**
  - Zentrale, strukturierte und unveränderliche Audit-Logs in der Datenbank
  - Logging von Auth-, Datenzugriffs- und Änderungsereignissen
  - Abfrage-/Filterpfade für Admin- und Security-Auswertungen

### Sprint 2 – Platform, Upload & Frontend Foundation
- **Story 7.2 / Issues #27, #29 – Infrastruktur & Developer Setup**
  - Docker-Compose-Provisionierung für PostgreSQL und MinIO mit Health Checks und Persistent Volumes
  - Dokumentierter Migrations-Workflow und Developer-Setup für lokale Entwicklung
- **Story 7.3 / Issue #23 – MinIO Storage Integration & Upload-Basis**
  - Objektpersistenz für Uploads in MinIO mit privater Ablage und deterministischen Keys
  - Fehlerpfade für Storage-Probleme und lokale Compose-Kompatibilität
  - Grundlage für ZIP-Upload-Verarbeitung und Dateiverknüpfung zu Nano-Entwürfen
- **Story 8.1 / Issues #30, #31, #32, #33, #34 – Frontend Foundation**
  - React-18-/Vite-/TypeScript-Bootstrap mit Strict-TS-Basis
  - Tailwind-CSS-Konfiguration mit Design-Tokens und Baseline-Styles
  - Routing-Skeleton für Kernrouten und Fallback-Seiten
  - Zentraler Axios-Client mit vorbereiteten JWT-Interceptor-Hookpoints
  - Frontend-Compose-Integration und produktionsfähiger Build-Output

### Sprint 3 – Core Nano Management & Landing Page
- **Story 2.2 / Issue #53 – Nano Metadata Capture**
  - Persistente Nano-Metadaten in PostgreSQL mit Validierung und GET/POST-Endpunkten
  - Unterstützung für Titel, Beschreibung, Kategorie, Level, Dauer, Sprache und weitere Metadaten
  - Editierbarkeit im Draft-Zustand als Grundlage für den Veröffentlichungsworkflow
- **Story 2.4 / Issue #52 – Nano Status Workflow**
  - Statusmodell für Nanos inklusive valider Zustandsübergänge
  - Veröffentlichung nur bei vollständigen Metadaten
  - Rechteprüfung pro Creator sowie Audit-Logging bei Statuswechseln
- **Story 8.2 / Issue #54 – Landing Page & Global Navigation**
  - Öffentliche Landing Page mit Hero-Bereich, Value Proposition und CTA-Buttons
  - Responsive globale Navigation mit Auth-Zuständen, Active Route Highlighting und Mobile-Menü
  - Sprachumschalter-Platzhalter, WCAG-orientierte Semantik und Docker-/Dev-Frontend-Anbindung

### Sprint 4 – Search Infrastruktur
- **Story 7.4 / Issue #62 – Redis Cache Setup (Self-Hosted) für Search**
  - Redis-basierter Search-Response-Cache für `/api/v1/search` mit TTL = 30 Minuten
  - Deterministische Cache-Key-Strategie auf Basis aller Suchparameter (`q`, `category`, `level`, `duration`, `page`, `limit`)
  - Cache-Invalidierung bei Nano-Metadaten- und Statusänderungen
  - Degraded Mode: Redis-Ausfall führt nicht zu API-Ausfall (Live-Search über Meilisearch als Fallback)
  - Observability-Hooks via strukturierte Cache hit/miss/store/invalidate Logs

## 🐳 Docker Services

**docker-compose.yml** - Vollständige Entwicklungsumgebung:
- PostgreSQL 13 (Port 5432)
- Redis 7 (Port 6379)
- MinIO (Port 9000/9001)
- Meilisearch v1.6.0 (Port 7700)
- FastAPI App (Port 8000)

```bash
# Services starten
docker-compose up -d

# Status prüfen (alle sollten "healthy" sein)
docker-compose ps

# Services stoppen
docker-compose down
```

**Zugriff**:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Meilisearch: http://localhost:7700

**Umgebungsvariablen**: Siehe `.env.example` für alle Konfigurationsoptionen.

## 📚 Wichtige API Endpoints

**Vollständige API-Dokumentation**: http://localhost:8000/docs

### Authentifizierung
- `POST /api/v1/auth/register` - User Registration
- `POST /api/v1/auth/login` - Login (JWT Access + Refresh Token)
- `POST /api/v1/auth/verify-email` - Email verifizieren
- `POST /api/v1/auth/refresh-token` - Token erneuern
- `POST /api/v1/auth/logout` - Logout

### Uploads
- `POST /api/v1/uploads/zip` - ZIP-Datei hochladen (authentifiziert, max. 50 MB)

### Audit
- `GET /api/v1/audit/logs` - Audit Logs abrufen (Admin)
- `GET /api/v1/audit/suspicious` - Verdächtige Aktivitäten (Admin)

## 🛠️ Technologie-Stack

| Komponente | Technologie | Version |
|------------|-------------|---------|
| Framework | FastAPI | 0.133.1 |
| Database ORM | SQLAlchemy | 2.0.47 |
| Validation | Pydantic | 2.12.5 |
| Auth | JWT (python-jose) | 3.3.0 |
| Password | passlib + bcrypt | 1.7.4 |
| DB (Prod) | PostgreSQL | 13+ |
| DB (Test) | SQLite | - |
| Testing | pytest + Vitest | pytest 9.0.2 / vitest 3.x |
| Objektspeicher | MinIO | 2024-12-13 |
| Suchmaschine | Meilisearch | 1.6.0 |
| Frontend | React + Vite + TypeScript + React Query | React 18 / Vite 5 / TanStack Query 5 |

## 📖 Weitere Dokumentation

### Developer Guides
- **[doc/DEVELOPER_SETUP.md](./doc/DEVELOPER_SETUP.md)** - **Comprehensive setup guide** for Sprint 2 (DB, MinIO, uploads, troubleshooting)
- **[doc/DATABASE_MIGRATIONS.md](./doc/DATABASE_MIGRATIONS.md)** - Alembic migration workflow and best practices

### Architecture & Implementation
- **[IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)** - Detaillierte Implementierungsdokumentation
- **[LEARNINGS.md](./LEARNINGS.md)** - Architektur-Entscheidungen und Erkenntnisse
- **[doc/planning/](./doc/planning/)** - Projektplanung und Requirements

### Feature-Specific Docs
- **[doc/AUDIT_LOGGING.md](./doc/AUDIT_LOGGING.md)** - Audit logging framework (40+ event types)
- **[doc/FRONTEND_S2_SETUP.md](./doc/FRONTEND_S2_SETUP.md)** - React + Vite + Tailwind setup (Story 8.1)
- **[doc/REACT_QUERY_SETUP.md](./doc/REACT_QUERY_SETUP.md)** - TanStack Query integration
- **[doc/SEARCH_CACHE.md](./doc/SEARCH_CACHE.md)** - Redis-Cache-Strategie für Search (TTL, Keys, Invalidierung, degraded mode)

## 🔒 Sicherheitsfeatures

- **Password Hashing**: Bcrypt (Cost: 12, OWASP-konform)
- **Account Lockout**: 3 Fehlversuche → 60 Min Sperre
- **Email Verification**: Pflicht vor Login (JWT, 24h gültig)
- **Session Management**: Access Token (15 Min) + Refresh Token (7 Tage)
- **Audit Logging**: Alle Security-Events mit IP, User-Agent, Timestamps

## 🔜 Nächste Schritte

### Geplante Stories
- **Story 1.2**: User Profile Management (CRUD, Avatar Upload)
- **Story 1.6**: GDPR Compliance (Datenexport, Löschung, Consent)
- **Story 2.x**: Nano Unit Management (Publizieren, Versionierung)
- **Story 3.x**: Marketplace & Discovery (Suche, Empfehlungen)

---

**Letzte Aktualisierung**: März 2026
