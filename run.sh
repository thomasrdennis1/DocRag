#!/usr/bin/env bash
# DocRAG Search — one-click launcher (macOS / Linux)
set -e

cd "$(dirname "$0")"

# Activate venv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Load .env if present
if [ -f ".env" ]; then
    set -a; source .env; set +a
fi

python run.py "$@"
