#!/usr/bin/env bash
# scripts/profiles/discard-web.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB="$ROOT/apps/web"
if [[ ! -d "$WEB" ]]; then
  echo "✓ Web frontend profile discarded (or skipped — contains real code)."
  exit 0
fi
# Heuristic: template stubs only — README + AGENTS, no package.json / src
if [[ -f "$WEB/package.json" ]] || [[ -d "$WEB/src" ]]; then
  echo "WARN: apps/web/ appears to contain real code — leaving in place."
else
  rm -rf "$WEB"
fi
echo "✓ Web frontend profile discarded (or skipped — contains real code)."
