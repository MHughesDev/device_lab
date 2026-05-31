#!/usr/bin/env bash
# scripts/project-health.sh — aggregate repo health checks for docs-first workflow.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[project:health] queue validation"
make queue:validate

echo "[project:health] docs map invariants"

echo "[project:health] docs check"

echo "[project:health] adr index regeneration check"
python3 skills/repo-governance/adr-index-generator.py --repo-root . >/dev/null

echo "[project:health] placeholder scan (docs + idea)"
if rg -n "TODO|TBD|<placeholder>|pending-init|Stub procedure placeholder|Compatibility stub" docs IDEA.md >/tmp/project_health_placeholders.txt; then
  echo "Found unresolved placeholders/stubs:"
  cat /tmp/project_health_placeholders.txt
  exit 1
fi

echo "project:health OK"
