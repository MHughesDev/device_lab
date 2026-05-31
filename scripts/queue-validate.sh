#!/usr/bin/env bash
# scripts/queue-validate.sh
# Validate queue CSV schema (see scripts/queue_validate.py).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/queue_validate.py"
