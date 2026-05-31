#!/usr/bin/env bash
# scripts/profiles/enable-scheduled-jobs.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCH="$ROOT/apps/api/app/scheduler"
mkdir -p "$SCH/jobs"
cat >"$SCH/__init__.py" <<'EOF'
# apps/api/app/scheduler/__init__.py
"""APScheduler integration stub."""
EOF
cat >"$SCH/scheduler.py" <<'EOF'
# apps/api/app/scheduler/scheduler.py
"""APScheduler setup — wire into FastAPI lifespan in a real deployment."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def scheduler_lifespan() -> AsyncIterator[None]:
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
EOF
cat >"$SCH/jobs/__init__.py" <<'EOF'
# apps/api/app/scheduler/jobs/__init__.py
"""Registered scheduled jobs."""
EOF
cat >"$SCH/jobs/example_job.py" <<'EOF'
# apps/api/app/scheduler/jobs/example_job.py
"""Example job stub."""

from __future__ import annotations


def example_tick() -> None:
    """Replace with real work."""
EOF
cat >"$SCH/README.md" <<'EOF'
# apps/api/app/scheduler/README.md

Scheduled jobs profile. Connect `scheduler_lifespan` to the app `lifespan` when ready.
EOF
echo "✓ Scheduled jobs profile enabled."
