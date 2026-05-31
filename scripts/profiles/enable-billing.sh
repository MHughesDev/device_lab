#!/usr/bin/env bash
# scripts/profiles/enable-billing.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/billing"
mkdir -p "$PKG"
cat >"$PKG/__init__.py" <<'EOF'
# packages/billing/__init__.py

from packages.billing.stripe_client import StripeClient

__all__ = ["StripeClient"]
EOF
cat >"$PKG/stripe_client.py" <<'EOF'
# packages/billing/stripe_client.py
"""Stripe client stub."""

from __future__ import annotations

from typing import Any


class StripeClient:
    """Stripe SDK wrapper — implement with stripe package."""

    async def create_customer(self, email: str) -> dict[str, Any]:
        return {"id": "cus_stub", "email": email}

    async def create_subscription(self, customer_id: str, price_id: str) -> dict[str, Any]:
        return {"id": "sub_stub", "customer": customer_id, "price": price_id}

    async def handle_webhook(self, payload: bytes, signature: str) -> dict[str, Any]:
        _ = signature
        return {"received": len(payload)}
EOF
cat >"$PKG/webhooks.py" <<'EOF'
# packages/billing/webhooks.py
"""Stripe webhook router stub."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["billing"])


@router.post("/stripe")
async def stripe_webhook(request: Request) -> dict[str, str]:
    _ = await request.body()
    return {"status": "stub"}
EOF
cat >"$PKG/models.py" <<'EOF'
# packages/billing/models.py
"""Billing enums — stub."""

from __future__ import annotations

from enum import Enum


class SubscriptionStatus(str, Enum):
    """Stripe-like subscription states."""

    INCOMPLETE = "incomplete"
    ACTIVE = "active"
    CANCELED = "canceled"
EOF
cat >"$PKG/README.md" <<'EOF'
# packages/billing/README.md

Billing profile — wire `StripeClient` and webhooks into the API app when ready.
EOF
echo "✓ Billing profile enabled — packages/billing/ scaffolded."
