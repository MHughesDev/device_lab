#!/usr/bin/env bash
# scripts/prompt-list.sh
# List prompt templates in prompts/*.md

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
find "$ROOT/prompts" -maxdepth 1 -name '*.md' ! -name 'README.md' -print | sort
