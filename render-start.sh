#!/bin/bash
set -e

# Ensure we're in the project root directory
cd /opt/render/project/src

export PYTHONPATH="${PYTHONPATH}:backend"

echo "Starting PDF2AudioBook deployment..."
echo "Working directory: $(pwd)"

# Run database migrations directly
echo "Running database migrations..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "DATABASE_URL is set, proceeding with migrations..."
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."

# Set alembic configuration
export ALEMBIC_CONFIG=alembic.ini

# Check if alembic.ini exists
if [ ! -f "alembic.ini" ]; then
    echo "ERROR: alembic.ini not found in $(pwd)"
    ls -la
    exit 1
fi

# Run migrations from project root
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Database migrations completed successfully"
else
    echo "Database migration failed - this might be normal if tables already exist"
    echo "Continuing with application startup..."
fi

# Start the application
echo "Starting FastAPI application..."
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 2
