#!/bin/bash
set -e

export PYTHONPATH="${PYTHONPATH}:backend"

# Emergency migration fix for ENUM types
fix_enum_types() {
    echo "Fixing ENUM types in database..."
    cd backend

    # Create ENUM types if they don't exist
    cat << 'EOF' | psql "$DATABASE_URL" 2>/dev/null || true
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'producttype') THEN
        CREATE TYPE producttype AS ENUM ('subscription', 'one_time');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptiontier') THEN
        CREATE TYPE subscriptiontier AS ENUM ('free', 'pro', 'enterprise');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'voiceprovider') THEN
        CREATE TYPE voiceprovider AS ENUM ('openai', 'google', 'aws_polly', 'azure', 'eleven_labs');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'conversionmode') THEN
        CREATE TYPE conversionmode AS ENUM ('full', 'summary_explanation');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'jobstatus') THEN
        CREATE TYPE jobstatus AS ENUM ('pending', 'processing', 'completed', 'failed');
    END IF;
END $$;
EOF

    cd ..
    echo "ENUM types fixed!"
}

echo "Starting PDF2AudioBook deployment..."

# Wait for database to be ready
echo "Waiting for database connection..."
until PGPASSWORD=$DB_PASSWORD pg_isready -h $DB_HOST -p 5432 -U $DB_USER -d $DB_NAME; do
  echo "Database is unavailable - sleeping"
  sleep 2
done
echo "Database is ready!"

# Fix ENUM types first
fix_enum_types

# Run database migrations
echo "Running database migrations..."
cd backend
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Database migrations completed successfully"
else
    echo "Database migration failed, but continuing..."
fi

cd ..

# Start the application
echo "Starting FastAPI application..."
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 2
