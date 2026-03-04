# DiWeiWei Nano-Marktplatz

Marktplatz für Nano-Lerneinheiten mit JWT-Authentifizierung, Audit-Logging und umfassenden Tests.

## 📊 Aktueller Stand

**Fertiggestellte Stories**: 1.1, 1.3, 1.4, 1.5, 7.2, 7.3 ✅
- ✅ User Registration & Login mit Email-Verifizierung
- ✅ Password Hashing (Bcrypt, OWASP-konform)
- ✅ Email Verification Flow (JWT-basiert)
- ✅ Audit Logging Framework (40+ Event-Typen)
- ✅ ZIP Upload API (Nano-Lerneinheiten hochladen)
- ✅ Nano Upload Domain Model mit Alembic Migrations

**Qualität**:
- 221/221 Tests bestanden (100%)
- 87.82% Code Coverage (Ziel: >70%)
- Black/isort Code-Formatierung
- PostgreSQL + SQLite Support

## 🚀 Quick Start

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

### Frontend starten (Story 8.1 Baseline)

```bash
# Frontend Workspace wechseln
cd frontend

# Dependencies installieren
npm install

# Dev Server starten (Vite)
npm run dev
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
```

## 📋 Implementierte Features

### Authentifizierung & Sicherheit
- **User Registration**: Email-Validierung, Passwort-Stärke-Prüfung
- **Login**: JWT-basiert (Access + Refresh Token)
- **Email Verification**: Pflicht vor erstem Login (JWT-Token, 24h gültig)
- **Account Lockout**: 3 Fehlversuche → 60 Min. Sperre
- **Password Hashing**: Bcrypt (Cost: 12)
- **Audit Logging**: Alle Auth-Events mit IP, User-Agent, Timestamps

### Nano Upload (Stories 7.2, 7.3)
- **ZIP Upload API**: `POST /api/v1/uploads/zip`
  - Authentifizierung erforderlich
  - Max. 50 MB Dateigröße
  - Validierung: ZIP-Format, index.html erforderlich
  - Async Upload mit Hash-Berechnung
- **Domain Model**: `NanoUpload` mit Alembic Migrations
  - Status Tracking (uploaded, processing, published, failed)
  - Versioning Support
  - File Hashing (SHA256)

## 🐳 Docker Services

**docker-compose.yml** - Vollständige Entwicklungsumgebung:
- PostgreSQL 13 (Port 5432)
- Redis 7 (Port 6380)
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
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)
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
| Testing | pytest | 9.0.2 |
| Objektspeicher | MinIO | 2024-12-13 |
| Suchmaschine | Meilisearch | 1.6.0 |
| Frontend | React + Vite + TypeScript | React 18 / Vite 5 |

## 📖 Weitere Dokumentation

- **[IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)** - Detaillierte Implementierungsdokumentation
- **[LEARNINGS.md](./LEARNINGS.md)** - Architektur-Entscheidungen und Erkenntnisse
- **[doc/planning/](./doc/planning/)** - Projektplanung und Requirements

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