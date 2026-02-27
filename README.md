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

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run authentication tests only
pytest tests/modules/auth/ -v

# Run specific test
pytest tests/modules/auth/test_auth_service.py::test_register_user_success -v

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

**Test Results**: 37/37 tests passing | 87% code coverage

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
  "token": "verification_token_here"
}

Response: 200 OK or 501 Not Implemented (placeholder)
```

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
- ✅ Email verification enforcement
- ✅ JWT-based authentication
- ✅ Account lockout mechanism
- ✅ Password strength validation
- ✅ Token refresh functionality

**Quality Metrics:**
- 37/37 tests passing (100% pass rate)
- 87% code coverage (exceeds 70% requirement)
- All acceptance criteria from issue #2 met
- Production-ready code quality

**Status**: Pull Request #7 ready for review and merge

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