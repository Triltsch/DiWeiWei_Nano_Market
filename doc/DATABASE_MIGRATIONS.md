# Database Migrations

## Overview

This project uses Alembic for database schema migrations. All schema changes should be managed through migrations rather than direct SQL or `create_all()` calls.

**Note**: This document focuses on migration mechanics and best practices. For complete environment setup including PostgreSQL, MinIO, and troubleshooting, see [DEVELOPER_SETUP.md](./DEVELOPER_SETUP.md).

## Setup

### Prerequisites

- PostgreSQL database running (Docker Compose recommended)
- `TEST_DB_URL` environment variable set (for local development)

### Initial Setup

Alembic is already configured and initialized in the `migrations/` directory.

## Configuration

### Alembic Configuration Files

- `alembic.ini` - Alembic configuration (database URL sourced from environment)
- `migrations/env.py` - Migration environment setup (configured for async SQLAlchemy)
- `migrations/versions/` - Directory containing migration scripts

### Database URL

The migration system automatically uses the database URL from your environment:

```bash
# For development/testing
export TEST_DB_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"

# For production
export DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname"
```

## Creating Migrations

### Auto-generate Migration from Model Changes

This is the recommended approach - Alembic will detect changes in your SQLAlchemy models:

```bash
# Set database URL
export TEST_DB_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"

# Generate migration
python -m alembic revision --autogenerate -m "Brief description of changes"
```

**Example:**
```bash
python -m alembic revision --autogenerate -m "Add user profile fields"
```

### Manual Migration Creation

For complex changes or data migrations:

```bash
python -m alembic revision -m "Description of changes"
```

Then edit the generated file in `migrations/versions/` to add your changes.

## Applying Migrations

### Upgrade to Latest Version

```bash
# Set database URL
export TEST_DB_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"

# Apply all pending migrations
python -m alembic upgrade head
```

### Upgrade/Downgrade to Specific Version

```bash
# Upgrade to specific revision
python -m alembic upgrade <revision_id>

# Downgrade to specific revision
python -m alembic downgrade <revision_id>

# Downgrade one step
python -m alembic downgrade -1

# Downgrade to base (remove all migrations)
python -m alembic downgrade base
```

## Migration History

### View Migration History

```bash
# Show current version
python -m alembic current

# Show migration history
python -m alembic history

# Show migration history with details
python -m alembic history --verbose
```

## Best Practices

### 1. Always Auto-generate First

Start with auto-generate and then review/edit the generated migration:

```bash
python -m alembic revision --autogenerate -m "Description"
```

### 2. Review Generated Migrations

Always review the generated migration file before applying:

- Check that all intended changes are captured
- Verify index definitions
- Ensure foreign key constraints are correct
- Add any custom operations (data migrations, etc.)

### 3. Test Migrations

Test both upgrade and downgrade paths:

```bash
# Test upgrade
python -m alembic upgrade head

# Test downgrade
python -m alembic downgrade -1

# Re-apply
python -m alembic upgrade head
```

### 4. PostgreSQL Enum Types

When working with PostgreSQL enum types:

- Auto-generated migrations create enum types automatically
- **Important:** Always add enum type cleanup to the `downgrade()` function:

```python
def downgrade() -> None:
    # Drop tables first
    op.drop_table("my_table")
    
    # Then drop enum types
    op.execute("DROP TYPE IF EXISTS myenumtype CASCADE")
```

### 5. Handle Existing Data

For migrations that affect existing data:

- Add data migration logic after schema changes
- Use `op.execute()` for custom SQL
- Consider adding data validators

## Common Issues

### Issue: Enum Type Already Exists

**Problem:** `asyncpg.exceptions.DuplicateObjectError: type "mytype" already exists`

**Solution:** Ensure the downgrade function drops enum types:

```python
def downgrade() -> None:
    op.drop_table("my_table")
    op.execute("DROP TYPE IF EXISTS mytype CASCADE")
```

### Issue: Migration Conflicts

**Problem:** Multiple developers created migrations with the same revision

**Solution:** Use `alembic merge` to resolve:

```bash
python -m alembic merge heads -m "Merge migrations"
```

### Issue: Database Out of Sync

**Problem:** Database schema doesn't match migration state

**Solution:**

1. Downgrade to base: `python -m alembic downgrade base`
2. Reapply migrations: `python -m alembic upgrade head`

Or manually stamp the current version:

```bash
python -m alembic stamp head
```

### Issue: Revision Is `head`, but Tables Are Missing

**Problem:** `alembic_version` is already at latest revision, but application tables (for example `users`, `nanos`) are missing in `public`.

**Cause:** Inconsistent local state (migration pointer advanced without complete schema materialization, often due to reused local volumes).

**Solution (local Compose PostgreSQL on 5432):**

```bash
# Reset revision pointer, then replay all migrations
DATABASE_URL="postgresql://diwei_user:diwei_password@localhost:5432/diwei_nano_market" python -m alembic stamp base
DATABASE_URL="postgresql://diwei_user:diwei_password@localhost:5432/diwei_nano_market" python -m alembic upgrade head

# Validate required core tables
docker compose exec -T postgres psql -U diwei_user -d diwei_nano_market -c "select tablename from pg_tables where schemaname='public' and tablename in ('users','nanos','nano_ratings','nano_comments') order by tablename;"
```

## Migration Testing

### Test Setup

The test fixtures in `tests/conftest.py` are configured to work with migrations:

- Tests clean up enum types before and after each test run
- Tests use `Base.metadata.create_all()` for fast setup
- Integration tests can run migrations if needed

### Running Tests with Migrations

```bash
export TEST_DB_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"
python -m pytest tests/
```

## Sprint 2 Migration Context

### Nano Upload Domain Model (71e6668b4da7)

**Migration**: `71e6668b4da7_add_nano_domain_models_for_upload_`  
**Sprint**: 2 (Stories 2.1, 7.2)  
**Purpose**: Enable Nano content management with versioning support

**Key Schema Elements**:

1. **`nanos` table**:
   - Tracks Nano learning units
   - Links to `users` table via `creator_id`
   - Stores MinIO object reference in `file_storage_path`
   - Status workflow: `DRAFT` → `PENDING_REVIEW` → `PUBLISHED` / `ARCHIVED` → `DELETED`
   - Version tracking: Semantic version string (e.g., `1.0.0`)

2. **Status Enum (`nanostatus`)**:
   - `DRAFT`: Initial (no upload yet)
   - `PENDING_REVIEW`: Awaiting moderation
   - `PUBLISHED`: Available in marketplace
   - `ARCHIVED`: Hidden but preserved
   - `DELETED`: Marked for deletion

3. **Related Models**:
   - `audit_logs`: System event and auth tracking
   - `categories`: Classification system
   - `nano_category_assignments`: M:N relationship

**Integration Points**:
- **MinIO**: `file_storage_path` points to object at `nanos/{nano_id}/content/{filename}`
- **Users**: Foreign key enforces creator must be registered user
- **Versioning**: `version` field uses semantic versioning (1.0.0, 1.1.0, etc.)

**Downgrade Behavior**:
```python
# Enum cleanup required
def downgrade() -> None:
    op.drop_table("nanos")
    op.execute("DROP TYPE IF EXISTS nanostatus CASCADE")
    # + other tables...
```

### Migration Dependencies

**Sprint 2 migrations depend on**:
- Docker Compose PostgreSQL service running (port 5432)
- Environment variables: `DATABASE_URL` or `TEST_DB_URL`
- No MinIO connection required for schema creation (only for upload API)

**Migration applies**:
- Before first upload API call
- After PostgreSQL service is healthy
- During CI/CD pipeline before tests

See [DEVELOPER_SETUP.md](./DEVELOPER_SETUP.md#7-apply-database-migrations) for setup context.

## Current Schema

### Revision History

1. **71e6668b4da7** - "Add Nano domain models for upload workflow" (Sprint 2)
   - Added `users`, `audit_logs`, `consent_audit` tables
   - Added `nanos`, `categories` tables
   - Added `nano_category_assignments` junction table
   - Created enum types: `userstatus`, `userrole`, `auditaction`, `consenttype`, `nanostatus`, `nanoformat`, `competencylevel`, `licensetype`

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- Project domain model: `doc/planning/04_domain_model.md`
