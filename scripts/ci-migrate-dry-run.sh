#!/usr/bin/env bash
# scripts/ci-migrate-dry-run.sh
# Local parity with CI job migrate-dry-run: SQLite SQL preview + apply (no broken pipe).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Match .github/workflows/ci.yml; override short env values (Settings requires len >= 8).
if [ -z "${JWT_SECRET_KEY:-}" ] || [ "${#JWT_SECRET_KEY}" -lt 8 ]; then
  export JWT_SECRET_KEY="test-only-key-for-ci-migrations"
fi
export PYTHONPATH=.

echo "== Alembic SQL preview (first 50 lines, SQLite URL) =="
export DATABASE_URL="sqlite+aiosqlite:///./migration_ci_preview.db"
SQL_PREVIEW="$(mktemp)"
(
  cd apps/api && python3 -m alembic upgrade head --sql
) >"$SQL_PREVIEW" 2>&1
head -n 50 "$SQL_PREVIEW"
rm -f "$SQL_PREVIEW"

echo ""
echo "== Alembic apply to fresh SQLite file (matches CI apply step) =="
rm -f "${ROOT}/migration_ci_preview.db" "${ROOT}/migration_ci_apply.db"
export DATABASE_URL="sqlite+aiosqlite:///./migration_ci_apply.db"
make migrate

echo "ci-migrate-dry-run: OK"
