#!/usr/bin/env bash
set -e

pip install -r backend/requirements.txt

# CHANGE this to your real FastAPI module path
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
