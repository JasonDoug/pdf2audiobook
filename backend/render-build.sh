#!/bin/bash
set -e

echo "🚀 Starting PDF2Audiobook backend build for Render..."

# Install dependencies using uv
echo "📦 Installing dependencies..."
uv sync --frozen --no-install-project

# Verify installation (don't run migrations here - database may not be available)
echo "✅ Verifying installation..."
uv run python -c "from main import app; print('✅ Application imports successfully')"

# Check if required environment variables are set
echo "🔍 Checking environment variables..."
required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY" "CLERK_PEM_PUBLIC_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment variables check passed"

echo "🎉 Build completed successfully!"
echo "Note: Database migrations will be run on first startup"