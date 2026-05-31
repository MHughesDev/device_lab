#!/usr/bin/env bash
# scripts/init-repo.sh
# Bootstrap dev environment: editable install + optional .env.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -e ".[dev]"
"$ROOT/scripts/generate-env.sh" || true
echo "Init complete. Run: make migrate && make dev"
