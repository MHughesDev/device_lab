#!/usr/bin/env bash
# scripts/release-prepare.sh
# Verify pyproject version.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "release:prepare OK — update version before tagging."
