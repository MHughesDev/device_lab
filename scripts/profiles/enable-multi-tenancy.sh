#!/usr/bin/env bash
# scripts/profiles/enable-multi-tenancy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEN="$ROOT/apps/api/app/tenancy"
if [[ ! -d "$ROOT/apps/api/app" ]]; then
  echo "ERROR: apps/api/app not found" >&2
  exit 1
fi
mkdir -p "$TEN"
if [[ ! -f "$TEN/context.py" ]]; then
  cat >"$TEN/context.py" <<'EOF'
# apps/api/app/tenancy/context.py
"""Tenant context (ContextVar) — stub for initialization engine."""

from __future__ import annotations

import contextvars
from uuid import UUID

current_tenant_id: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    "current_tenant_id", default=None
)
EOF
fi
if [[ ! -f "$TEN/README.md" ]]; then
  cat >"$TEN/README.md" <<'EOF'
# apps/api/app/tenancy/README.md

Multi-tenancy module. This repository may already ship with `TenantContextMiddleware` and models — extend rather than replace.
EOF
fi
echo "✓ Multi-tenancy profile enabled — tenancy module checked."
