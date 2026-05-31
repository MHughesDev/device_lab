#!/usr/bin/env bash
# scripts/profiles/discard-multi-tenancy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEN="$ROOT/apps/api/app/tenancy"
if [[ ! -d "$TEN" ]]; then
  echo "✓ Multi-tenancy profile discarded."
  exit 0
fi
if [[ -f "$TEN/models.py" ]] && grep -q "class Tenant(" "$TEN/models.py" 2>/dev/null; then
  echo "WARN: tenancy/ contains real models — leaving in place."
else
  rm -rf "$TEN"
fi
echo "✓ Multi-tenancy profile discarded."
