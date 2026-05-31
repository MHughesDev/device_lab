#!/usr/bin/env bash
# scripts/profiles/discard-search.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/search"
if [[ -d "$PKG" ]] && [[ -f "$PKG/README.md" ]] && grep -q "Search profile" "$PKG/README.md"; then
  rm -rf "$PKG"
fi
echo "✓ Search profile discarded."
