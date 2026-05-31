#!/usr/bin/env bash
# scripts/profiles/discard-websocket.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RT="$ROOT/apps/api/app/realtime"
if [[ ! -d "$RT" ]]; then
  echo "✓ WebSocket profile discarded."
  exit 0
fi
if [[ -f "$RT/router.py" ]] && grep -q "WebSocket profile stub" "$RT/README.md" 2>/dev/null; then
  rm -rf "$RT"
else
  echo "WARN: realtime/ may contain custom code — leaving in place."
fi
echo "✓ WebSocket profile discarded."
