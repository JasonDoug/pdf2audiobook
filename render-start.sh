#!/bin/bash
set -e

export PYTHONPATH="${PYTHONPATH}:backend"

echo "Starting PDF2AudioBook deployment..."

# Wait for database to be ready
echo "Waiting for database connection..."
if [ -n "$DATABASE_URL" ]; then
    # Extract connection info from DATABASE_URL
    db_host=$(echo $DATABASE_URL | sed -n 's/.*:\/\/.*@\(.*\):.*/\1/p')
    db_port=$(echo $DATABASE_URL | sed -n 's/.*:\/\//user:pass@/; s/.*@.*:\([0-9]*\).*/\1/p')

    echo "Checking database connection to $db_host:$db_port"
    until pg_isready -h "$db_host" -p "$db_port" -q; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
    echo "Database is ready!"
else
    echo "DATABASE_URL not set, skipping database check"
fi

# Run database migrations
echo "Running database migrations..."
cd backend

# Check if alembic is available
if command -v alembic >/dev/null 2>&1; then
    alembic upgrade head
    echo "Database migrations completed"
else
    echo "Alembic not found, skipping migrations"
fi

cd ..

# Start the application
echo "Starting FastAPI application..."
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 2
```

Now let me commit this fix:

```bash
git add render-start.sh
git commit -m "Fix database connection in deployment script

- Simplified pg_isready command to use extracted host/port from DATABASE_URL
- Added better error handling for missing environment variables
- Made database check more robust for Render environment

This should resolve the 'too many command-line arguments' error."
git push origin main
```

The issue was that the `pg_isready` command syntax was incorrect. The error "too many command-line arguments (first is '5432')" indicates that the parameters were being passed in the wrong order or format.

The new script:
1. **Extracts host and port** properly from the `DATABASE_URL`
2. **Uses simpler pg_isready syntax** with just `-h` and `-p` flags
3. **Adds better error handling** for missing environment variables
4. **Maintains the same functionality** while being more robust

This should fix the database connection issue and allow the deployment to proceed successfully.
