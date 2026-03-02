# Database Migrations

Alembic database migrations for DiWeiWei Nano Market.

## Quick Start

```bash
# Set database URL
export TEST_DB_URL="postgresql+asyncpg://testuser:testpassword@localhost:5433/diweiwei_test"

# Apply migrations
python -m alembic upgrade head

# Create new migration (after changing models)
python -m alembic revision --autogenerate -m "Description"
```

## Documentation

See [doc/DATABASE_MIGRATIONS.md](../doc/DATABASE_MIGRATIONS.md) for complete migration guide.

## Directory Structure

```
migrations/
├── versions/          # Migration scripts
│   └── 71e6668b4da7_add_nano_domain_models_for_upload_.py
├── env.py            # Migration environment (configured for async)
├── script.py.mako    # Migration template
└── README            # This file
```

## Configuration

- Database URL sourced from `DATABASE_URL` or `TEST_DB_URL` environment variable
- Migrations use async SQLAlchemy (asyncpg driver)
- Black code formatter auto-applied to generated migrations
