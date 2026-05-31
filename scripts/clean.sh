#!/usr/bin/env bash
# scripts/clean.sh
# Remove common build artifacts and caches.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov build dist .eggs *.egg-info
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
rm -f .coverage coverage.xml 2>/dev/null || true
echo "Clean complete."
