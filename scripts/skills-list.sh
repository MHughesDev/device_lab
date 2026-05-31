#!/usr/bin/env bash
# scripts/skills-list.sh
# List skills by category (skills/*/).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for dir in "$ROOT/skills"/*/; do
  [[ -d "$dir" ]] || continue
  name=$(basename "$dir")
  echo "## $name"
  find "$dir" -maxdepth 1 -name '*.md' -print | sort | sed "s|^$ROOT/||"
done
