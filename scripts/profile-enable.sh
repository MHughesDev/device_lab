#!/usr/bin/env bash
# scripts/profile-enable.sh
# Resolve optional profile enablement (see skills/init/profile-resolver.py).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PROFILE="${PROFILE:-}"
if [[ -z "$PROFILE" ]]; then
  echo "Usage: PROFILE=<name> make profile:enable" >&2
  echo "Available profiles: web, mobile, ai, worker" >&2
  exit 1
fi

exec python3 "$ROOT/skills/init/profile-resolver.py" --repo-root "$ROOT" --profile "$PROFILE" "$@"
