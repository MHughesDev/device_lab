#!/usr/bin/env bash
# scripts/profiles/enable-email.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/notifications"
mkdir -p "$PKG/templates"
cat >"$PKG/__init__.py" <<'EOF'
# packages/notifications/__init__.py

from packages.notifications.factory import get_notification_provider

__all__ = ["get_notification_provider"]
EOF
cat >"$PKG/base.py" <<'EOF'
# packages/notifications/base.py
"""Notification provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    """Send transactional messages."""

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError
EOF
cat >"$PKG/smtp.py" <<'EOF'
# packages/notifications/smtp.py
"""SMTP stub."""

from __future__ import annotations

from packages.notifications.base import NotificationProvider


class SMTPProvider(NotificationProvider):
    async def send_email(self, to: str, subject: str, body: str) -> None:
        _ = (to, subject, body)
EOF
cat >"$PKG/sendgrid.py" <<'EOF'
# packages/notifications/sendgrid.py
"""SendGrid stub."""

from __future__ import annotations

from packages.notifications.base import NotificationProvider


class SendGridProvider(NotificationProvider):
    async def send_email(self, to: str, subject: str, body: str) -> None:
        _ = (to, subject, body)
EOF
cat >"$PKG/factory.py" <<'EOF'
# packages/notifications/factory.py
"""Resolve provider from EMAIL_PROVIDER."""

from __future__ import annotations

import os

from packages.notifications.base import NotificationProvider
from packages.notifications.smtp import SMTPProvider


def get_notification_provider() -> NotificationProvider:
    provider = os.environ.get("EMAIL_PROVIDER", "smtp")
    if provider == "smtp":
        return SMTPProvider()
    raise NotImplementedError(provider)
EOF
echo "Welcome" >"$PKG/templates/welcome.txt"
cat >"$PKG/README.md" <<'EOF'
# packages/notifications/README.md

Email / notifications profile — wire templates and providers in application code.
EOF
echo "✓ Email/notifications profile enabled — packages/notifications/ scaffolded."
