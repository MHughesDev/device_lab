#!/usr/bin/env bash
# scripts/queue-analyze.sh
# Validate queue CSV then run full queue intelligence analysis.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/scripts/queue_validate.py" || exit 1
exec python3 "$ROOT/skills/agent-ops/queue-intelligence.py" analyze --repo-root "$ROOT"
