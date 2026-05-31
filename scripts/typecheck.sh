#!/usr/bin/env bash
# scripts/typecheck.sh
# Run mypy in strict mode.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m mypy apps/api/app packages \
  scripts/scaffold-module.py
