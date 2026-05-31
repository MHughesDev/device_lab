#!/usr/bin/env bash
# scripts/release-verify.sh
# Run lint, typecheck, test before release tag.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/lint.sh"
"$ROOT/scripts/fmt-check.sh"
"$ROOT/scripts/typecheck.sh"
"$ROOT/scripts/test.sh"
echo "release:verify OK"
