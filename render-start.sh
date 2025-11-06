#!/bin/bash
set -e

echo "🚀 Starting PDF2Audiobook backend on Render..."

# Change to backend directory
cd backend

# Run database migrations on startup
echo "🗄️ Running database migrations..."
uv run alembic upgrade head

echo "✅ Database migrations completed"

# Start the application
echo "🌟 Starting FastAPI application..."
exec uv run uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4