#!/usr/bin/env bash
# scripts/profiles/enable-analytics.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/analytics"

if [[ -d "$PKG" ]]; then
  echo "packages/analytics/ already exists — skipping scaffold."
else
  mkdir -p "$PKG"
  cat >"$PKG/__init__.py" <<'EOF'
# packages/analytics/__init__.py
"""Analytics profile — event tracking interface."""

from packages.analytics.tracker import AnalyticsTracker, track

__all__ = ["AnalyticsTracker", "track"]
EOF

  cat >"$PKG/tracker.py" <<'EOF'
# packages/analytics/tracker.py
"""Analytics event tracker stub.

Replace the no-op implementation with your analytics provider
(e.g. Segment, Amplitude, PostHog) when ready.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsEvent:
    """Typed analytics event."""

    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    user_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class AnalyticsTracker:
    """No-op analytics tracker — wire a real provider in settings."""

    def __init__(self, write_key: str | None = None, enabled: bool = False) -> None:
        self._write_key = write_key
        self._enabled = enabled

    def track(self, event: AnalyticsEvent) -> None:
        if not self._enabled:
            logger.debug("analytics disabled — event dropped: %s", event.name)
            return
        # TODO: replace with real provider call (Segment, PostHog, etc.)
        logger.info("analytics event: %s properties=%s", event.name, event.properties)

    def identify(self, user_id: str, traits: dict[str, Any] | None = None) -> None:
        if not self._enabled:
            return
        logger.info("analytics identify: user=%s traits=%s", user_id, traits or {})


def track(name: str, properties: dict[str, Any] | None = None, user_id: str | None = None) -> None:
    """Module-level convenience — logs only; wire to a real tracker in production."""
    logger.info("analytics.track name=%s user=%s props=%s", name, user_id, properties or {})
EOF

  cat >"$PKG/models.py" <<'EOF'
# packages/analytics/models.py
"""Analytics enums and value types."""

from __future__ import annotations

from enum import Enum


class EventCategory(str, Enum):
    """Top-level event categories."""

    USER = "user"
    BILLING = "billing"
    FEATURE = "feature"
    ERROR = "error"
    SYSTEM = "system"
EOF

  cat >"$PKG/README.md" <<'EOF'
# packages/analytics/README.md

Analytics profile — event tracking interface.

Wire `AnalyticsTracker` with your analytics provider (Segment, PostHog, Amplitude)
by setting `ANALYTICS_WRITE_KEY` and `ANALYTICS_ENABLED=true` in `.env`.
EOF
fi

echo "✓ Analytics profile enabled — packages/analytics/ scaffolded."
