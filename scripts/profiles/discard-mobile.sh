#!/usr/bin/env bash
# scripts/profiles/discard-mobile.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
M="$ROOT/apps/mobile"
if [[ ! -d "$M" ]]; then
  echo "✓ Mobile profile discarded (or skipped — contains real code)."
  exit 0
fi
if [[ -f "$M/package.json" ]] || [[ -d "$M/app" ]]; then
  echo "WARN: apps/mobile/ appears to contain real code — leaving in place."
else
  rm -rf "$M"
fi
echo "✓ Mobile profile discarded (or skipped — contains real code)."
