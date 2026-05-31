#!/usr/bin/env bash
# scripts/install-hooks.sh
# Install pre-commit hooks. Run once after cloning.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v pre-commit &>/dev/null; then
  echo "Installing pre-commit..."
  pip install pre-commit
fi

pre-commit install
echo "Hooks installed. Run 'pre-commit run --all-files' to verify."
