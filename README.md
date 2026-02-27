# DiWeiWei Nano-Marktplatz

A modern, scalable marketplace platform for nano-learning units (Nano-Lerneinheiten) with user authentication, JWT-based security, and comprehensive testing.

## 📋 Project Overview

DiWeiWei is a decentralized nano-learning marketplace where creators can share bite-sized learning units with consumers. The project is built with production-ready architecture from day one, implementing security best practices and comprehensive testing.

**Current Status**: Story 1.1 (User Registration & Login) ✅ Complete
- 37/37 tests passing
- 87% code coverage
- All acceptance criteria met
- Pull Request #7 ready for merge

## 🚀 Quick Start

### Prerequisites

- Python 3.13.1+
- pip or pip3
- PostgreSQL 13+ (for production; SQLite used for testing)

### Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Triltsch/DiWeiWei_Nano_Market.git
   cd DiWeiWei_Nano_Market
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   
   **On Windows (PowerShell):**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   
   **On macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r pyproject.toml
   # or
   pip install -e .
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Database Configuration

The application supports multiple database configurations for different scenarios:

#### Development (Default Local PostgreSQL)
For development with a local PostgreSQL database on standard port 5432:
```bash
# In .env
DATABASE_URL="postgresql://user:password@localhost:5432/diwei_nano_market"
```

#### Docker Compose (Integration Testing)
When running PostgreSQL via Docker Compose on port 5433:
```bash
# In .env
TEST_DB_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"
```

Or set it as environment variable before running the app:

**Windows (PowerShell):**
```powershell
$env:TEST_DB_URL = "postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"
python -m uvicorn app.main:app --reload
```

**macOS/Linux:**
```bash
export TEST_DB_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"
python -m uvicorn app.main:app --reload
```

#### Production
For production deployments, set DATABASE_URL with your production database:
```bash
# In .env or production secrets
DATABASE_URL="postgresql://user:password@your-prod-host:5432/diweiwei_production"
ENV="production"
SECRET_KEY="your-strong-secret-key-here"
```

**Configuration Priority:**
1. `TEST_DB_URL` (Docker Compose, if set)
2. `DATABASE_URL` (Production/Development, if set)
3. Default based on ENV (sqlite for tests, localhost:5432 for others)

### Database Initialization

After configuring your database connection, you must initialize the database schema before running the application.

#### Option 1: Using Initialization Script (Recommended)

Simple Python script that creates all necessary tables:

```bash
# From project root directory
python scripts/init_db.py

# Expected output:
# ✅ Database schema created successfully!
# Tables created:
#   - users
#   - audit_logs (future)
```

#### Option 2: Alembic Migrations

When migrations are available, use Alembic for version-controlled schema changes:

```bash
# Display current database version
alembic current

# Run all pending migrations
alembic upgrade head

# Verify tables were created
psql -h localhost -p 5433 -U testuser -d diweiwei_test -c "\dt"
```

#### Option 3: Manual Schema Creation

Direct SQLAlchemy table creation (advanced):

```bash
python -c "
import asyncio
from app.database import engine
from app.models import Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print('✅ Database schema created successfully!')

asyncio.run(init_db())
"
```

#### Option 4: Docker Compose PostgreSQL (Reset &amp; Reinitialize)

To completely reset the Docker Compose test database and start fresh:

```bash
# Stop and remove the container and its data
docker-compose -f docker-compose.test.yml down -v

# Start fresh PostgreSQL container
docker-compose -f docker-compose.test.yml up -d

# Initialize schema using Option 1 above
python scripts/init_db.py
```

**Verification:**
```bash
# Check if tables exist and have data (after running tests or registering users)
docker-compose -f docker-compose.test.yml exec postgres \
  psql -U testuser -d diweiwei_test -c "SELECT COUNT(*) FROM users;"
```

### Running the Application

**Development server with auto-reload:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production server:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Access API Documentation

- **Interactive Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🐳 Docker Setup

Docker is required to run integration tests with PostgreSQL. Follow the steps below to install and verify Docker on your system.

### Installation

#### Windows

1. **Download Docker Desktop**
   - Visit [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
   - Download the installer for your system (Intel or Apple Silicon)

2. **Install Docker Desktop**
   - Run the installer and follow the installation wizard
   - Ensure "Install required Windows components for WSL 2 backend" is checked
   - Complete the installation and restart your computer

3. **Verify Installation**
   ```powershell
   docker --version
   docker run hello-world
   ```

#### macOS

1. **Download Docker Desktop**
   - Visit [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - Download for Intel or Apple Silicon

2. **Install Docker Desktop**
   - Drag the Docker.app to the Applications folder
   - Launch Docker from Applications

3. **Verify Installation**
   ```bash
   docker --version
   docker run hello-world
   ```

#### Linux (Ubuntu/Debian)

```bash
# Update package manager
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Add current user to docker group (logout and login required)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker-compose --version
docker run hello-world
```

### Verify Docker & Docker Compose

```bash
# Check Docker installation
docker --version
# Expected output: Docker version X.X.X

# Check Docker Compose installation
docker-compose --version
# Expected output: Docker Compose version X.X.X

# Test Docker is running
docker ps
# Should show a list of containers (empty if no containers are running)
```

### Start Docker Daemon

- **Windows/macOS**: Docker Desktop runs automatically after installation. Launch it from your applications menu if it's not running.
- **Linux**: Start Docker service manually if needed:
  ```bash
  sudo systemctl start docker
  sudo systemctl status docker  # Verify it's running
  ```

### Project Docker Compose Setup

This project includes a `docker-compose.test.yml` file for running PostgreSQL integration tests. The configuration provides an isolated test database environment.

#### Project Docker Images

The project uses:
- **PostgreSQL 13 Alpine**: Lightweight PostgreSQL image optimized for testing
  - Container name: `diweiwei_test_db`
  - Port: `5433` (mapped to PostgreSQL's default `5432`)
  - Credentials: `testuser` / `testpassword`
  - Database: `diweiwei_test`

#### Quick Start with Docker Compose

```bash
# Start PostgreSQL test container in the background
docker-compose -f docker-compose.test.yml up -d

# Check container status (wait for "healthy" state)
docker-compose -f docker-compose.test.yml ps

# View logs (useful for debugging startup)
docker-compose -f docker-compose.test.yml logs postgres

# Stop the container
docker-compose -f docker-compose.test.yml down

# Remove container and volumes (clean reset)
docker-compose -f docker-compose.test.yml down -v
```

#### Monitor Container Health

```bash
# Check if PostgreSQL is ready
docker-compose -f docker-compose.test.yml ps

# Look for: "postgres ... Up (healthy)"
# Container takes 5-25 seconds to be fully ready
```

#### Connect to PostgreSQL for Manual Testing

```bash
# Enter PostgreSQL shell (requires psql client)
psql -h localhost -p 5433 -U testuser -d diweiwei_test

# Or use docker exec to run psql inside container
docker-compose -f docker-compose.test.yml exec postgres \
  psql -U testuser -d diweiwei_test -c "SELECT version();"
```

#### Troubleshooting Docker Compose

```bash
# Port 5433 already in use
# Option 1: Stop conflicting service
docker ps | grep 5433
docker stop <container-id>

# Option 2: Use different port by editing docker-compose.test.yml
# Change "5433:5432" to "5434:5432"

# Container fails to start
docker-compose -f docker-compose.test.yml logs postgres

# Clean up all Docker artifacts (careful!)
docker-compose -f docker-compose.test.yml down -v
docker system prune -a
```

## 🧪 Testing

### Unit Tests (SQLite)

Run the fast unit tests using in-memory SQLite:

```bash
# Run all unit tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run unit tests only (skip integration tests)
pytest tests/ -m "not integration" -v

# Run authentication tests only
pytest tests/modules/auth/ -v

# Run specific test
pytest tests/modules/auth/test_auth_service.py::test_register_user_success -v

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Integration Tests (PostgreSQL)

Integration tests validate real database interactions with PostgreSQL. They require Docker Compose and a running PostgreSQL container.

**Prerequisites:**
- Docker and Docker Compose installed and running
- See [Project Docker Compose Setup](#project-docker-compose-setup) section above

**Complete Workflow:**

```bash
# 1. Start PostgreSQL test container (in the project directory)
docker-compose -f docker-compose.test.yml up -d

# 2. Wait for PostgreSQL to be ready (look for "healthy" status)
docker-compose -f docker-compose.test.yml ps

# 3. Run integration tests with PostgreSQL
TEST_DB_URL=postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test \
  pytest tests/ -m integration -v

# 4. Stop the container when done
docker-compose -f docker-compose.test.yml down
```

**Integration Test Coverage:**
- Full registration and login flow with real DB constraints
- Email verification enforcement
- Account lockout mechanism validation
- Email and username uniqueness constraints
- Real PostgreSQL dialect behavior validation

**Combined Testing (Unit + Integration):**

```bash
# Start PostgreSQL container
docker-compose -f docker-compose.test.yml up -d

# Run all tests (unit + integration)
TEST_DB_URL=postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test \
  pytest tests/ -v --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Stop PostgreSQL container
docker-compose -f docker-compose.test.yml down
```

### Test Results

**Current Status**: 37+ unit tests passing | 87%+ code coverage

## 📚 API Endpoints

### Authentication

#### Register User
```http
POST /api/v1/auth/register

{
  "email": "user@example.com",
  "username": "testuser",
  "password": "SecurePass123!",
  "first_name": "Test",
  "preferred_language": "de"
}

Response: 201 Created
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "testuser",
  "email_verified": false,
  "created_at": "2026-02-27T10:00:00+00:00",
  ...
}

Possible error response when database is unavailable:

Response: 503 Service Unavailable
{
  "detail": "Service temporarily unavailable. Please try again later."
}
```

#### Login
```http
POST /api/v1/auth/login

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh-token

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Verify Email
```http
POST /api/v1/auth/verify-email

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response: 200 OK
{
  "message": "Email verified successfully. You can now login.",
  "email": "user@example.com"
}

Error: 401 Unauthorized
{
  "detail": "Invalid or expired email verification token"
}
```

#### Resend Verification Email
```http
POST /api/v1/auth/resend-verification-email

{
  "email": "user@example.com"
}

Response: 200 OK
{
  "message": "(MVP) Verification token generated. Copy this token to verify your email: eyJ0eXAiOiJKV1QiLCJhbGc...",
  "email": "user@example.com"
}

Error: 401 Unauthorized
{
  "detail": "Email already verified"
}
```

### Email Verification Flow

The system implements JWT-based email verification for enhanced security:

**Registration → Verification → Login Flow:**
1. User registers with `POST /api/v1/auth/register` 
2. User receives unverified status (`email_verified: false`)
3. User cannot login until email is verified (receives 403 Forbidden)
4. User requests verification token via `POST /api/v1/auth/resend-verification-email`
5. User verifies email with `POST /api/v1/auth/verify-email` using token
6. After verification, user can successfully login

**Token Details:**
- **Type**: JWT (JSON Web Token)
- **Expiration**: 24 hours (configurable via `EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS`)
- **Format**: Same algorithm (HS256) as access/refresh tokens
- **Payload**: Contains user_id and email

**MVP Status:** 
In the current MVP implementation, the verification token is returned in the API response (for manual testing). 
In production, the token would be sent via email with a verification link.

### Health Check

```http
GET /health

Response: 200 OK
{
  "status": "ok",
  "version": "0.1.0"
}
```

## 📁 Project Structure

```
DiWeiWei_Nano_Market/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application factory
│   ├── config.py                 # Pydantic settings
│   ├── database.py               # SQLAlchemy async session
│   ├── models/
│   │   └── __init__.py          # SQLAlchemy ORM models (User entity)
│   ├── modules/
│   │   ├── auth/                # Authentication module
│   │   │   ├── router.py        # FastAPI routes
│   │   │   ├── service.py       # Business logic
│   │   │   ├── password.py      # Password hashing
│   │   │   ├── tokens.py        # JWT token management
│   │   │   └── validators.py    # Custom validators
│   │   └── users/               # User management (future)
│   └── schemas/
│       └── __init__.py          # Pydantic request/response models
├── tests/                         # Test suite
│   ├── conftest.py              # Pytest fixtures
│   └── modules/auth/
│       ├── test_auth_service.py # Service layer tests (20)
│       └── test_auth_routes.py  # Route layer tests (17)
├── doc/                           # Project documentation
│   └── planning/                 # Planning & requirements
├── pyproject.toml                # Project configuration & dependencies
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore rules
├── LEARNINGS.md                  # Architecture decisions & insights
├── IMPLEMENTATION_STATUS.md      # Detailed implementation docs
└── README.md                     # This file
```

## 🔐 Security Features

### Password Security
- **Hashing**: Bcrypt (primary) with PBKDF2-HMAC-SHA256 fallback
- **Strength Validation**: 8+ chars, uppercase, digit, special character
- **Salt**: Unique salt per password (bcrypt default)

### Account Security
- **Account Lockout**: 3 failed login attempts → 60 minute lockout
- **Email Verification**: Required before login
- **Session Management**: Short-lived access tokens (15 min) + long-lived refresh tokens (7 days)

### Configuration Security
- **Environment Variables**: Secrets and configuration are primarily managed via `.env`
- **Production Requirement**: `SECRET_KEY` must be set explicitly in production
- **TLS Ready**: Infrastructure prepared for HTTPS enforcement

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.133.1 |
| Database ORM | SQLAlchemy | 2.0.47 |
| Data Validation | Pydantic | 2.12.5 |
| Authentication | JWT (python-jose) | 3.3.0 |
| Password Hashing | passlib + bcrypt | 1.7.4 |
| Database (Prod) | PostgreSQL + asyncpg | 13+ |
| Database (Test) | SQLite + aiosqlite | - |
| Testing | pytest | 9.0.2 |
| Code Quality | black, isort | Latest |

## 📖 Documentation

- **[IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)** - Detailed implementation documentation, architecture decisions, and test analysis
- **[LEARNINGS.md](./LEARNINGS.md)** - Key learnings from prototype analysis and implementation decisions
- **[doc/planning/](./doc/planning/)** - Project planning, requirements, and architecture documents

## 🎯 Current Implementation Status

### Story 1.1: User Registration & Login ✅ **COMPLETE**

**Features Implemented:**
- ✅ User registration with validation
- ✅ Email verification enforcement (Issue #13)
- ✅ Email verification endpoint implementation
- ✅ JWT-based authentication
- ✅ Account lockout mechanism
- ✅ Password strength validation
- ✅ Token refresh functionality

**Quality Metrics:**
- 63/63 tests passing (100% pass rate)
- 87.18% code coverage (exceeds 70% requirement)
- All acceptance criteria from issue #2 met
- Email verification feature fully implemented (Issue #13)
- Production-ready code quality

**Recent Changes (Issue #13 - Email Verification):**
- Added `create_email_verification_token()` for JWT token generation
- Implemented `POST /api/v1/auth/verify-email` endpoint
- Implemented `POST /api/v1/auth/resend-verification-email` endpoint
- Added `verify_email_with_token()` service function
- Created comprehensive test suite (16 new tests)
- Updated documentation with verification flow

**Status**: Story 1.1 complete, ready for Story 1.2 (User Profile Management)

## 🔜 Next Steps

### Story 1.2: User Profile Management (Planned)
- User profile CRUD operations
- Preferred learning preferences
- Learning history tracking
- Profile customization

### Future Stories
- Story 2.x: Nano Unit Management
- Story 3.x: Marketplace & Discovery
- Story 4.x: Chat & Communication
- Story 5.x: Reviews & Ratings

## 🚨 Troubleshooting

### Virtual Environment Not Activating
```powershell
# Set execution policy (Windows only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Database Connection Error
- Ensure PostgreSQL is running (for production)
- Update `DATABASE_URL` in `.env`
- For development, tests use in-memory SQLite automatically

### Database Schema Error: "relation \"users\" does not exist"

**Error:**
```
asyncpg.exceptions.UndefinedTableError: relation "users" does not exist
```

**Solution:**
1. Initialize the database schema (see [Database Initialization](#database-initialization) section)
2. Run Alembic migrations: `alembic upgrade head`
3. Or manually create schema: See Database Initialization → Option 2

### Database Connection to Docker Compose Fails

**Error:**
```
OSError: Multiple exceptions: [Errno 10061] Connect call failed ('127.0.0.1', 5432)
```

**Likely causes:**
- Using wrong port (5432 instead of 5433 for Docker Compose)
- PostgreSQL container not running
- Wrong connection credentials

**Solutions:**
1. Set `TEST_DB_URL` with correct port 5433
2. Verify Docker container is running: `docker-compose -f docker-compose.test.yml ps`
3. Check credentials match docker-compose.test.yml
4. See [Database Configuration](#database-configuration) section

### Bcrypt Version Warning

**Warning:**
```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**Impact**: Warning only - non-blocking, application continues to work normally

**Workaround**: Upgrade bcrypt and passlib to compatible versions (future fix planned)

### Port Already in Use
```bash
# Use a different port
python -m uvicorn app.main:app --reload --port 8001
```

### Import Errors
```bash
# Reinstall dependencies
pip install -e . --force-reinstall
```

## 📝 Development Workflow

1. **Create feature branch**: `git checkout -b feature/description`
2. **Make changes** and **add tests**
3. **Run tests**: `pytest tests/ -v`
4. **Format code**: `black app/ tests/`
5. **Organize imports**: `isort app/ tests/`
6. **Commit**: `git commit -m "feature: description"`
7. **Push**: `git push origin feature/description`
8. **Create Pull Request** on GitHub

## 📄 License

This project is part of the DiWeiWei initiative for decentralized nano-learning marketplace experimentation.

## 👥 Contributors

- Development Team (2026)

## ❓ Questions & Support

For questions, issues, or suggestions:
1. Check [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for technical details
2. Review [LEARNINGS.md](./LEARNINGS.md) for architecture decisions
3. Open an issue on GitHub with detailed information
4. Create a discussion in the GitHub repository

---

**Last Updated**: February 27, 2026
**Current Branch**: Story 1.1 Complete - Ready for Merge