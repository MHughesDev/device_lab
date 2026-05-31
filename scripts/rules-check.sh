#!/usr/bin/env bash
# scripts/rules-check.sh
# Verify .cursor/rules/*.md have YAML front matter.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ERR=0
for f in "$ROOT/.cursor/rules"/*.md; do
  [[ -f "$f" ]] || continue
  if ! head -n1 "$f" | grep -q '^---$'; then
    echo "Missing front matter: $f" >&2
    ERR=1
  fi
done
exit "$ERR"
