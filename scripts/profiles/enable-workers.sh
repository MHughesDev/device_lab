#!/usr/bin/env bash
# scripts/profiles/enable-workers.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASKS="$ROOT/packages/tasks"
if [[ ! -d "$TASKS" ]]; then
  mkdir -p "$TASKS"
  echo "# packages/tasks/__init__.py" >"$TASKS/__init__.py"
  echo "# packages/tasks/README.md" >"$TASKS/README.md"
fi

python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
dc = root / "docker-compose.yml"
text = dc.read_text()
if "worker:" in text and "redis:" in text:
    print("worker/redis services already in docker-compose.yml")
    raise SystemExit(0)
block = """

  redis:
    image: redis:7-alpine
    profiles:
      - worker
    ports:
      - "6379:6379"

  worker:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    profiles:
      - worker
    env_file:
      - .env
    command: ["celery", "-A", "apps.api.src.worker", "worker", "--loglevel=info"]
    depends_on:
      - redis
      - api
    environment:
      CELERY_BROKER_URL: ${CELERY_BROKER_URL:-redis://redis:6379/0}
      CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND:-redis://redis:6379/1}
"""
marker = "\n\nvolumes:\n  api_data:"
if marker not in text:
    raise SystemExit("docker-compose.yml: expected root volumes section marker")
text = text.replace(marker, block + marker, 1)
dc.write_text(text)
print("Patched docker-compose.yml with redis + worker")
PY

echo "✓ Workers profile enabled — Redis and worker services added to Compose."
