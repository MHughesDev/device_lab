#!/usr/bin/env bash
# scripts/docs-generate.sh
# Manual human/AI-agent tool: run documentation generation on demand, never from CI.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/skills/repo-governance/docs-generator.py" --mode generate --repo-root "$ROOT"
