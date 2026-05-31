#!/usr/bin/env bash
# scripts/profiles/discard-email.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/notifications"
if [[ -d "$PKG" ]] && [[ -f "$PKG/README.md" ]] && grep -q "Email / notifications profile" "$PKG/README.md"; then
  rm -rf "$PKG"
fi
echo "✓ Email/notifications profile discarded."
