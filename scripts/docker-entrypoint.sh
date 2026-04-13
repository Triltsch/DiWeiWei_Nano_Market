#!/bin/bash
# Docker entrypoint script for app container
# Initializes database and starts the application

set -e

echo "🚀 Starting DiWeiWei Nano Market backend..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
python <<'PY'
import asyncio
import os

import asyncpg


async def wait_for_postgres() -> None:
  host = os.getenv("POSTGRES_HOST", "postgres")
  user = os.getenv("POSTGRES_USER", "diwei_user")
  password = os.getenv("POSTGRES_PASSWORD", "diwei_password")
  database = os.getenv("POSTGRES_DB", "diwei_nano_market")

  for _ in range(60):
    try:
      conn = await asyncpg.connect(
        host=host,
        user=user,
        password=password,
        database=database,
      )
      await conn.close()
      return
    except Exception:
      print("   PostgreSQL is unavailable - sleeping", flush=True)
      await asyncio.sleep(2)

  raise SystemExit("PostgreSQL did not become available in time")


asyncio.run(wait_for_postgres())
PY

echo "✅ PostgreSQL is up!"

# Initialize database tables if they don't exist
echo "🔧 Initializing database schema..."
set +e  # Temporarily disable exit-on-error to handle init_db failure gracefully
python /app/scripts/init_db.py
INIT_STATUS=$?
set -e  # Re-enable exit-on-error

if [ $INIT_STATUS -eq 0 ]; then
  echo "✅ Database initialized successfully!"
else
  echo "⚠️  Database initialization had issues, but continuing..."
fi

# Start the application
echo "🎯 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
