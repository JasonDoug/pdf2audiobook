#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:backend"
alembic upgrade 1e025f228445
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 4
