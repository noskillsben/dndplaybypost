#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding foundational data..."
python seed_data.py

echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
