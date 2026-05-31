#!/usr/bin/env bash
# scripts/profiles/discard-scheduled-jobs.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCH="$ROOT/apps/api/app/scheduler"
if [[ -d "$SCH" ]] && [[ -f "$SCH/README.md" ]] && grep -q "Scheduled jobs profile" "$SCH/README.md"; then
  rm -rf "$SCH"
fi
echo "✓ Scheduled jobs profile discarded."
