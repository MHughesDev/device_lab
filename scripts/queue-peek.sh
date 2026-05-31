#!/usr/bin/env bash
# scripts/queue-peek.sh
# Print first lines of queue.csv (title comment, header, first row).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$ROOT/queue/queue.csv"

if [[ ! -f "$FILE" ]]; then
  echo "Missing $FILE" >&2
  exit 1
fi

head -n 3 "$FILE"
