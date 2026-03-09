#!/bin/bash
# Docker entrypoint script for app container
# Initializes database and starts the application

set -e

echo "🚀 Starting DiWeiWei Nano Market backend..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD="${POSTGRES_PASSWORD:-diwei_password}" psql -h postgres -U "${POSTGRES_USER:-diwei_user}" -d "${POSTGRES_DB:-diwei_nano_market}" -c '\q' 2>/dev/null; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is up!"

# Initialize database tables if they don't exist
echo "🔧 Initializing database schema..."
python /app/scripts/init_db.py

if [ $? -eq 0 ]; then
  echo "✅ Database initialized successfully!"
else
  echo "⚠️  Database initialization had issues, but continuing..."
fi

# Start the application
echo "🎯 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
