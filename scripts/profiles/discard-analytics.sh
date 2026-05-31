#!/usr/bin/env bash
# scripts/profiles/discard-analytics.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/analytics"

if [[ -d "$PKG" ]]; then
  rm -rf "$PKG"
  echo "✓ Analytics profile discarded — packages/analytics/ removed."
else
  echo "Analytics profile not present — nothing to discard."
fi
