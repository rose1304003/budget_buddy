#!/usr/bin/env bash
set -e

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

# pick the correct module path
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
