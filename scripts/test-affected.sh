#!/usr/bin/env bash
# scripts/test-affected.sh
# Run pytest with testmon to only test code affected by changes.
# Usage: make test:affected (or scripts/test-affected.sh)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Running pytest with testmon (tests affected by code changes only)..."
python3 -m pytest --testmon -x -q "$@"
