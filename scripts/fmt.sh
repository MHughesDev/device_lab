#!/usr/bin/env bash
# scripts/fmt.sh
# Apply Ruff formatting (modifies files in place).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m ruff format apps/api/app packages \
  scripts/scaffold-module.py
