#!/usr/bin/env bash
# scripts/dev.sh
# Start the API with uvicorn reload (requires: pip install -e ., optional .env).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]] && [[ -f .env.example ]]; then
  echo "Note: no .env found; copy .env.example to .env or export DATABASE_URL / JWT_SECRET_KEY." >&2
fi

export PYTHONPATH="${ROOT}/apps/api"
cd "${ROOT}/apps/api"
exec python3 -m uvicorn app.main:app --reload --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"
