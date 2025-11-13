#!/bin/bash
set -e

export PYTHONPATH="${PYTHONPATH}:backend"

echo "Starting PDF2AudioBook deployment..."

# Run database migrations directly
echo "Running database migrations..."
cd backend

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "DATABASE_URL is set, proceeding with migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Database migrations completed successfully"
else
    echo "Database migration failed - this might be normal if tables already exist"
    echo "Continuing with application startup..."
fi

cd ..

# Start the application
echo "Starting FastAPI application..."
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 2
