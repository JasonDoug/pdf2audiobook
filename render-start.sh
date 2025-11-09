#!/bin/bash
set -e
set -x # Print commands

echo "🚀 Starting PDF2Audiobook backend on Render..."

# Set PYTHONPATH to include backend directory
export PYTHONPATH="${PYTHONPATH}:backend"

# Run database migrations on startup (only if DATABASE_URL is set)
if [ -n "$DATABASE_URL" ]; then
    echo "🗄️ Running database migrations..."
    uv run alembic upgrade head
else
    echo "⚠️ DATABASE_URL not set, skipping database migrations"
fi

# Start the application
echo "🌟 Starting FastAPI application..."
if command -v uv &> /dev/null; then
    exec uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 4
else
    exec uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 4
fi
