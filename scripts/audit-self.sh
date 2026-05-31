#!/usr/bin/env bash
# scripts/audit-self.sh
# Run repository self-audit (scripts/repo_self_audit.py).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/repo_self_audit.py" --repo-root "$ROOT"
