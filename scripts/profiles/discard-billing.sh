#!/usr/bin/env bash
# scripts/profiles/discard-billing.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/billing"
if [[ -d "$PKG" ]] && [[ -f "$PKG/README.md" ]] && grep -q "Billing profile" "$PKG/README.md"; then
  rm -rf "$PKG"
fi
echo "✓ Billing profile discarded."
