#!/usr/bin/env bash
# scripts/profiles/enable-web.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$ROOT/apps/web"
if [[ ! -f "$ROOT/apps/web/README.md" ]]; then
  cat >"$ROOT/apps/web/README.md" <<'EOF'
<!-- apps/web/README.md -->
# apps/web

Web frontend profile. Enabled by initialization engine.

Framework: see IDEA.md §5.
EOF
fi
if [[ ! -f "$ROOT/apps/web/AGENTS.md" ]]; then
  cat >"$ROOT/apps/web/AGENTS.md" <<'EOF'
<!-- apps/web/AGENTS.md -->
# apps/web/AGENTS.md

## Purpose

Optional React (or other) web client for this repository.

## Profiles

Enabled when the web frontend profile is active.

## Commands

See root `Makefile` and `docs/development/local-setup.md`.

## Rules

Follow `skills/frontend/` playbooks; do not bypass API contracts in `packages/contracts/`.
EOF
fi
echo "✓ Web frontend profile scaffolded."
