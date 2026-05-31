#!/usr/bin/env bash
# scripts/profiles/enable-websocket.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RT="$ROOT/apps/api/app/realtime"
mkdir -p "$RT"
cat >"$RT/__init__.py" <<'EOF'
# apps/api/app/realtime/__init__.py
"""Real-time / WebSocket module."""

from apps.api.src.realtime.router import router

__all__ = ["router"]
EOF
cat >"$RT/connection_manager.py" <<'EOF'
# apps/api/app/realtime/connection_manager.py
"""WebSocket connection manager stub."""

from __future__ import annotations


class ConnectionManager:
    """Track active WebSocket connections."""

    def __init__(self) -> None:
        self._connections: list[object] = []

    async def connect(self, websocket: object) -> None:
        self._connections.append(websocket)

    def disconnect(self, websocket: object) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
EOF
cat >"$RT/router.py" <<'EOF'
# apps/api/app/realtime/router.py
"""WebSocket routes stub."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.api.src.realtime.connection_manager import ConnectionManager

router = APIRouter(tags=["realtime"])
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
EOF
cat >"$RT/README.md" <<'EOF'
# apps/api/app/realtime/README.md

WebSocket profile stub. Register `router` in `main.py` when enabling real-time features.
EOF
echo "✓ WebSocket profile enabled — realtime module scaffolded."
