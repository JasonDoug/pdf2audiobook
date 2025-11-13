#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:backend"
uv run alembic upgrade head
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 4
