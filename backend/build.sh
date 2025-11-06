#!/bin/bash
set -e

echo "🚀 Starting PDF2Audiobook backend deployment build..."

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --frozen --no-install-project

# Run database migrations
echo "🗄️ Running database migrations..."
uv run alembic upgrade head

# Verify installation
echo "✅ Verifying installation..."
uv run python -c "from main import app; print('✅ Application imports successfully')"

echo "🎉 Build completed successfully!"