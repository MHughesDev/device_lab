#!/usr/bin/env bash
# scripts/db-reset.sh
# Reset the Postgres dev database via docker compose, then re-apply migrations
# and seed initial superuser data. Requires Docker.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to reset the Postgres dev database." >&2
  exit 1
fi

echo "Stopping and removing db volume..."
docker compose down -v db 2>/dev/null || docker compose down -v

echo "Starting db..."
docker compose up -d db

echo "Waiting for db to become healthy..."
for i in {1..30}; do
  if docker compose ps db --format json 2>/dev/null | grep -q '"Health":"healthy"'; then
    break
  fi
  sleep 1
done

echo "Running prestart (migrations + initial superuser) in backend container..."
docker compose run --rm prestart

echo "Database reset complete."
