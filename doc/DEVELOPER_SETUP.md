# Developer Setup Guide - Sprint 2

## Overview

This guide covers the complete local development environment setup for the DiWeiWei Nano-Marktplatz project, with focus on Sprint 2 components:
- **Database**: PostgreSQL 13 with Alembic migrations
- **Object Storage**: MinIO (S3-compatible)
- **Caching**: Redis 7
- **Search**: Meilisearch 1.6
- **Upload System**: ZIP validation and storage

## Prerequisites

### Required Software
- **Python 3.13.1+** - Backend runtime
- **Docker Desktop** - For local infrastructure services (PostgreSQL, Redis, MinIO, Meilisearch)
- **Node.js 18+** - Frontend development (optional for backend-only work)
- **Git** - Version control

### Recommended Tools
- **VS Code** - Project includes tasks and configuration
- **PowerShell 7+** (Windows) or **Bash** (macOS/Linux) - For task execution
- **HTTPie or Postman** - API testing

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/Triltsch/DiWeiWei_Nano_Market.git
cd DiWeiWei_Nano_Market
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install project in editable mode with all dependencies
pip install -e .

# Verify installation
python -c "import fastapi; print(f'FastAPI {fastapi.__version__} installed successfully')"
```

## Environment Configuration

### 4. Configure Environment Variables

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your preferred editor
```

**Critical settings to review:**

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-unsafe-change-me` | **CHANGE THIS** for production |
| `DATABASE_URL` | *(not set)* | PostgreSQL connection (auto-detected from Docker) |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO API endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key (application client) |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret key (application client) |
| `MINIO_BUCKET_NAME` | `nanos` | Default upload bucket |
| `MEILI_MASTER_KEY` | `diweiwei-dev-master-key...` | Meilisearch API key |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO server root user (Docker Compose only) |
| `MINIO_ROOT_PASSWORD` | `minioadmin123` | MinIO server root password (Docker Compose only) |

**Important**: For local development, leave `DATABASE_URL` and `REDIS_URL` unset in `.env`. The application will auto-detect services from Docker Compose.

### Environment-Specific Configuration

#### Local Development (Host Machine)
When running the backend on your host machine (outside Docker):
- Redis: `REDIS_URL=redis://localhost:6379/0`
- PostgreSQL: Auto-detected via Docker health checks
- MinIO: `MINIO_ENDPOINT=localhost:9000`, `MINIO_SECURE=false`

#### Docker Compose
When running the full stack in Docker (via `docker-compose up`):
- Redis: `REDIS_URL=redis://redis:6379/0` (service name)
- PostgreSQL: `postgresql://diwei_user:diwei_password@postgres:5432/diwei_nano_market`
- MinIO: `MINIO_ENDPOINT=minio:9000`

**Best Practice**: Leave `REDIS_URL` unset in `.env` and use `REDIS_HOST`/`REDIS_PORT` instead. Docker Compose will override these via service environment variables.

## Infrastructure Setup

### 5. Start Docker Services

```bash
# Pull all images (verify availability)
docker compose pull

# Start all services in background
docker compose up -d

# Verify all services are healthy
docker compose ps
```

Expected output (all services should show "healthy"):
```
NAME                     STATUS
diwei_dev_app           Up (healthy)
diwei_dev_postgres      Up (healthy)
diwei_dev_redis         Up (healthy)
diwei_dev_minio         Up (healthy)
diwei_dev_meilisearch   Up (healthy)
diwei_dev_minio_init    Exited (0)
```

**Health Check Wait Time**: Services typically reach healthy status in 10-30 seconds. If a service shows "starting" after 60 seconds, see [Troubleshooting](#common-setup-failures).

### 6. Verify Service Connectivity

```bash
# Test PostgreSQL (from host machine)
docker exec diwei_dev_postgres pg_isready -U diwei_user -d diwei_nano_market

# Test Redis
docker exec diwei_dev_redis redis-cli ping

# Test MinIO (requires curl)
curl -f http://localhost:9000/minio/health/live
```

### Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **API (FastAPI)** | http://localhost:8000 | N/A |
| **API Docs (Swagger)** | http://localhost:8000/docs | N/A |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin123` |
| **Meilisearch** | http://localhost:7700 | Master key from `.env` |
| **PostgreSQL** | `localhost:5432` | `diwei_user` / `diwei_password` |
| **Redis** | `localhost:6379` | No auth (dev mode) |

## Database Migrations

### 7. Apply Database Migrations

```bash
# Run migrations to set up schema
python -m alembic upgrade head

# Verify current migration version
python -m alembic current
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade -> 71e6668b4da7, add nano domain models for upload flow
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
71e6668b4da7 (head)
```

### Migration Workflow

#### View Migration History
```bash
# Show all migrations
python -m alembic history

# Show current version
python -m alembic current
```

#### Create New Migration
```bash
# Auto-generate from SQLAlchemy model changes
python -m alembic revision --autogenerate -m "Brief description"

# Review generated file in migrations/versions/
# Edit if needed, then apply:
python -m alembic upgrade head
```

#### Rollback Migration
```bash
# Downgrade one step
python -m alembic downgrade -1

# Downgrade to specific revision
python -m alembic downgrade <revision_id>

# Downgrade to base (remove all)
python -m alembic downgrade base
```

**Best Practice**: Always review auto-generated migrations before applying. Alembic detects schema changes but may miss data migrations or require manual enum cleanup in downgrade functions.

See [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) for comprehensive migration documentation.

## MinIO Object Storage Setup

### 8. Verify MinIO Bucket Creation

MinIO bucket creation happens automatically via the `minio_init` service. Verify:

```bash
# Check minio_init service completed successfully
docker compose ps minio_init

# Expected: "Exited (0)" status
```

**Manual bucket verification:**

1. Open MinIO Console: http://localhost:9001
2. Login with credentials: `minioadmin` / `minioadmin123`
3. Navigate to **Buckets** → Verify `nanos` bucket exists
4. Check bucket policy is set to **private** (default)

### Testing Upload to MinIO

```bash
# Test MinIO connectivity from Python
python -c "
from minio import Minio
client = Minio(
    'localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin123',
    secure=False
)
print('Buckets:', [b.name for b in client.list_buckets()])
"
```

Expected output: `Buckets: ['nanos']`

### MinIO Configuration in Application

The app uses `MinIOStorageAdapter` for all object storage operations:
- **Upload**: `POST /api/v1/upload/nano` → stores in `nanos/{nano_id}/content/{filename}`
- **Deterministic paths**: Same `nano_id` overwrites previous upload (idempotent)
- **Retry logic**: 3 attempts for transient failures
- **Timeout**: 10 minutes per upload operation

## Upload System Prerequisites

### 9. Understanding Upload Flow

**Upload Workflow (Story 2.1):**

1. **Authentication**: User must be logged in (JWT access token)
2. **ZIP Validation**: File must be valid ZIP with supported content (`.pdf`, `.jpg`, `.png`, `.mp4`, `.webm`)
3. **Size Limit**: Max 100 MB per upload
4. **Storage**: File uploaded to MinIO at deterministic path
5. **Database**: `Nano` record created with `DRAFT` status

### Testing Upload Endpoint

```bash
# 1. Register and login to get access token
# (See API docs: http://localhost:8000/docs)

# 2. Create test ZIP file (PowerShell)
$testContent = 'Test Nano Content'
$testContent | Out-File -FilePath test-content.pdf -Encoding utf8
Compress-Archive -Path test-content.pdf -DestinationPath test-nano.zip -Force
Remove-Item test-content.pdf

# 3. Upload ZIP (replace TOKEN with your access token)
curl -X POST http://localhost:8000/api/v1/upload/nano \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@test-nano.zip"
```

Expected response:
```json
{
  "nano_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "draft",
  "message": "Upload successful"
}
```

### Upload Domain Model

The `Nano` model (migration `71e6668b4da7`) includes:
- **id**: UUID primary key
- **creator_id**: Foreign key to users table
- **status**: Enum (`DRAFT`, `PENDING_REVIEW`, `PUBLISHED`, `ARCHIVED`, `DELETED`)
- **file_storage_path**: MinIO object path
- **version**: Semantic version string (e.g., `1.0.0`)
- **format**: Content format (`VIDEO`, `TEXT`, `QUIZ`, `INTERACTIVE`, `MIXED`)
- **competency_level**: Learning level (`BASIC`, `INTERMEDIATE`, `ADVANCED`)
- **title**, **description**, **duration_minutes**, **language**
- Timestamps: `created_at`, `updated_at`

## Running the Application

### 10. Start Backend Server

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access API documentation: http://localhost:8000/docs

### 11. Run Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test suite
pytest tests/modules/auth/ -v

# Run only integration tests (requires Docker services)
pytest tests/ -v -m integration

# Run only unit tests (fast, no Docker required)
pytest tests/ -v -m unit

# Generate coverage report
# View: htmlcov/index.html
```

**Important**: Use the `Test: Verified` VS Code task instead of raw `pytest` to ensure Docker services are healthy before running tests. This prevents false passes when Redis/PostgreSQL aren't ready.

### 12. Code Quality Checks

```bash
# Format code with Black
python -m black app tests

# Sort imports with isort
python -m isort app tests

# Check formatting (CI mode)
python -m black --check app tests
python -m isort --check-only app tests

# Run all quality checks
# Use VS Code task: "Checks"
```

## Common Setup Failures

This section documents frequent issues and their solutions, extracted from production learnings.

### Issue 1: Docker Services Not Starting

**Symptom**: `docker compose up -d` hangs or services show "unhealthy"

**Possible Causes**:

1. **Port conflicts**: Another service using 5432, 6379, 9000, etc.
   ```bash
   # Check port usage (Windows)
   netstat -ano | findstr :5432
   
   # Check port usage (macOS/Linux)
   lsof -i :5432
   ```
   **Solution**: Stop conflicting service or change ports in `docker-compose.yml`

2. **Insufficient Docker resources**: Not enough memory/CPU
   **Solution**: Increase Docker Desktop resources (Settings → Resources)

3. **Old volumes with incompatible data**: Persisted data from different service versions
   ```bash
   # Stop services and remove volumes
   docker compose down -v
   
   # Restart fresh
   docker compose up -d
   ```

### Issue 2: MinIO Bucket Not Created

**Symptom**: Upload fails with "Bucket does not exist" error

**Diagnosis**:
```bash
# Check minio_init service logs
docker compose logs minio_init
```

**Common Causes**:

1. **Credential mismatch**: `minio_init` service uses wrong credentials
   **Solution**: Verify `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` match in both `minio` and `minio_init` services

2. **MinIO not healthy when init runs**
   **Solution**: Restart services to trigger re-initialization:
   ```bash
   docker compose restart minio_init
   ```

3. **Network issues**: Init container can't reach MinIO service
   **Solution**: Check Docker network:
   ```bash
   docker network inspect diweiwei_nano_market_diwei_dev
   ```

### Issue 3: Database Migration Fails with "Type Already Exists"

**Symptom**: `alembic upgrade head` fails with:
```
asyncpg.exceptions.DuplicateObjectError: type "nanostatus" already exists
```

**Root Cause**: PostgreSQL enum types aren't cleaned up by previous downgrade

**Solution**:
```bash
# Drop enum types manually
docker exec -it diwei_dev_postgres psql -U diwei_user -d diwei_nano_market
\c diwei_nano_market
DROP TYPE IF EXISTS nanostatus CASCADE;
\q

# Re-run migration
python -m alembic upgrade head
```

**Prevention**: Always include enum cleanup in migration downgrade functions:
```python
def downgrade() -> None:
    op.drop_table("nanos")
    op.execute("DROP TYPE IF EXISTS nanostatus CASCADE")
```

### Issue 4: Redis Connection Refused

**Symptom**: Tests fail with:
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Possible Causes**:

1. **Redis service not running**
   ```bash
   docker compose ps redis
   # Should show "Up (healthy)"
   ```

2. **Wrong Redis port in configuration**
   **Check**: `.env` should have `REDIS_PORT=6379` (not 6380 or other)

3. **Environment variables not loaded**
   **Solution**: Ensure `.env` file exists and is loaded:
   ```bash
   # Test manual load
   export $(cat .env | xargs)
   pytest tests/
   ```

4. **Docker Compose app container using localhost instead of service name**
   **Solution**: In `docker-compose.yml`, explicitly override:
   ```yaml
   environment:
     REDIS_URL: "redis://redis:6379/0"  # Use service name, not localhost
   ```

### Issue 5: Upload Timeout After 10 Minutes

**Symptom**: Upload request times out with no error before completion

**Root Cause**: Application enforces 10-minute timeout for upload operations (Issue #26)

**Solutions**:

1. **Reduce file size**: Current limit is 100 MB
2. **Check network speed**: Upload speed affects total time
3. **Increase timeout** (not recommended): Modify `UPLOAD_TIMEOUT_SECONDS` in `.env`

**Debug**:
```bash
# Check MinIO server logs for slow writes
docker compose logs minio

# Monitor upload progress
curl -X POST http://localhost:8000/api/v1/upload/nano \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@large-file.zip" \
  --trace-time
```

### Issue 6: Meilisearch Health Check Fails

**Symptom**: `curl http://localhost:7700/health` returns error or times out

**Possible Causes**:

1. **Meilisearch container not running or unhealthy**
   **Solution**: Verify the container status and call the unauthenticated `/health` endpoint:
   ```bash
   docker compose ps meilisearch
   docker compose logs meilisearch
   curl http://localhost:7700/health
   ```

2. **Volume version incompatibility**: Old Meilisearch data format
   ```bash
   # Check logs for version mismatch
   docker compose logs meilisearch
   
   # If incompatible, remove volume and restart
   docker compose down
   docker volume rm diweiweiwei_nano_market_meilisearch_data
   docker compose up -d
   ```

### Issue 7: Tests Pass Locally But Fail in CI

**Common Causes**:

1. **Tests not waiting for Docker services**: Use `Test: Verified` task which includes health checks
2. **Environment variables not set in CI**: Check GitHub Actions secrets/vars
3. **Dependency version mismatch**: Pin versions in `pyproject.toml`
4. **Bcrypt version incompatibility**: Passlib requires bcrypt `>=4.0.1,<4.1` (Issue #4)

**CI Debugging**:
```bash
# Run tests exactly as CI does
docker compose up -d
sleep 10  # Wait for health checks
pytest tests/ -v --tb=short
```

### Issue 8: PostgreSQL "Too Many Connections"

**Symptom**: Application can't connect, PostgreSQL logs show connection limit reached

**Root Cause**: Connection pool not properly closed in tests or crashes

**Solution**:
```bash
# View active connections
docker exec -it diwei_dev_postgres psql -U diwei_user -d diwei_nano_market \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
docker exec -it diwei_dev_postgres psql -U diwei_user -d diwei_nano_market \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# Or restart PostgreSQL
docker compose restart postgres
```

**Prevention**: Ensure all test fixtures properly clean up database sessions:
```python
@pytest.fixture
async def db_session():
    async with async_session_maker() as session:
        yield session
    await session.close()  # Always close
```

## Stopping and Cleaning Up

### Stop Services
```bash
# Stop all services (keep volumes)
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Stop and remove images too
docker compose down -v --rmi all
```

### Reset Development Environment
```bash
# Complete reset (WARNING: destroys all data)
docker compose down -v
docker system prune -af
docker volume prune -f

# Restart from scratch
docker compose pull
docker compose up -d
python -m alembic upgrade head
```

## Next Steps

### Development Workflow
1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Make changes**: Edit code following project guidelines
3. **Run quality checks**: Use VS Code `Checks` task
4. **Run tests**: Use VS Code `Test: Verified` task
5. **Commit**: `git commit -m "feat: description"`
6. **Push**: `git push origin feature/your-feature`

### Sprint 2 Frontend Setup
See [FRONTEND_S2_SETUP.md](./FRONTEND_S2_SETUP.md) for React + Vite + Tailwind setup instructions (Story 8.1).

### Additional Documentation
- **[DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md)** - Comprehensive Alembic migration guide
- **[AUDIT_LOGGING.md](./AUDIT_LOGGING.md)** - Audit logging framework documentation
- **[REACT_QUERY_SETUP.md](./REACT_QUERY_SETUP.md)** - Frontend data fetching setup
- **[README.md](../README.md)** - Project overview and quick start
- **[LEARNINGS.md](../LEARNINGS.md)** - Architecture decisions and lessons learned

## Getting Help

### Useful Commands
```bash
# View all Docker service logs
docker compose logs

# Follow logs for specific service
docker compose logs -f postgres

# Check health status
docker compose ps

# Connect to PostgreSQL shell
docker exec -it diwei_dev_postgres psql -U diwei_user -d diwei_nano_market

# Connect to Redis CLI
docker exec -it diwei_dev_redis redis-cli

# List MinIO buckets
docker run --rm --network diweiwei_nano_market_diwei_dev \
  minio/mc alias set myminio http://minio:9000 minioadmin minioadmin123 && \
  minio/mc ls myminio
```

### Resources
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/
- **Alembic Migrations**: https://alembic.sqlalchemy.org/
- **MinIO Python SDK**: https://min.io/docs/minio/linux/developers/python/minio-py.html
- **Project Issues**: https://github.com/Triltsch/DiWeiWei_Nano_Market/issues

---

**Last Updated**: 2026-03-08 (Sprint 2 - Issue #29)  
**Maintainer**: Development Team  
**Feedback**: Open an issue or PR with improvements
