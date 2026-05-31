#!/usr/bin/env bash
# scripts/profiles/enable-mobile.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$ROOT/apps/mobile"
if [[ ! -f "$ROOT/apps/mobile/README.md" ]]; then
  cat >"$ROOT/apps/mobile/README.md" <<'EOF'
<!-- apps/mobile/README.md -->
# apps/mobile

Mobile (Expo) profile. Enabled by initialization engine.

See IDEA.md §5.
EOF
fi
if [[ ! -f "$ROOT/apps/mobile/AGENTS.md" ]]; then
  cat >"$ROOT/apps/mobile/AGENTS.md" <<'EOF'
<!-- apps/mobile/AGENTS.md -->
# apps/mobile/AGENTS.md

## Purpose

Optional Expo / React Native client.

## Profiles

Mobile profile.

## Commands

See root documentation and Expo tooling.

## Rules

Follow `skills/frontend/expo-auth-storage.md` for token handling.
EOF
fi
echo "✓ Mobile profile scaffolded."
