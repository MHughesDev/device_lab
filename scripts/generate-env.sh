#!/usr/bin/env bash
# scripts/generate-env.sh
# Copy .env.example to .env if .env is missing.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  echo ".env already exists; not overwriting."
  exit 0
fi
if [[ ! -f .env.example ]]; then
  echo "Missing .env.example" >&2
  exit 1
fi
cp .env.example .env
echo "Created .env from .env.example — edit secrets before use."
