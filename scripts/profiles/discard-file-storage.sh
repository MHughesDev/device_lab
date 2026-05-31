#!/usr/bin/env bash
# scripts/profiles/discard-file-storage.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/storage"
if [[ -d "$PKG" ]] && [[ -f "$PKG/README.md" ]] && grep -q "File storage profile" "$PKG/README.md"; then
  rm -rf "$PKG"
fi
echo "✓ File storage profile discarded."
