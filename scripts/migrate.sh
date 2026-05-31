#!/usr/bin/env bash
# scripts/migrate.sh
# Run Alembic migrations against the configured database.
# Operates from apps/api (where alembic.ini lives).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/apps/api"
cd "$ROOT/apps/api"

if [[ "${1:-}" == "create" ]]; then
  if [[ -z "${MESSAGE:-}" ]]; then
    echo "Usage: MESSAGE='description' make migrate:create" >&2
    exit 1
  fi
  exec python3 -m alembic revision --autogenerate -m "${MESSAGE}"
fi

exec python3 -m alembic upgrade head
