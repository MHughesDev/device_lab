# device_logs.py — WS/SSE log-stream route: GET /api/v1/devices/{id}/logs/stream (Phase 08)
from __future__ import annotations
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import Device, DeviceLogEvent, DeviceLogEventPublic

router = APIRouter(prefix="/devices", tags=["device-logs"])


def _get_device_or_404(db, device_id: uuid.UUID) -> Device:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.websocket("/{device_id}/logs/stream")
async def stream_device_logs_ws(
    device_id: uuid.UUID,
    websocket: WebSocket,
    level: str | None = Query(default=None),
    source: str | None = Query(default=None),
    since: str | None = Query(default=None),
) -> None:
    """WebSocket: replay ring buffer then stream live device log events.

    Bound to loopback only via the control-plane localhost invariant — the API
    server itself only binds to 127.0.0.1, so no further per-route enforcement is
    needed beyond the global binding.

    Query params:
      level  — filter by level (debug|info|warn|error)
      source — filter by source (lifecycle|provisioner|transport|mcp|ledger|…)
      since  — ISO timestamp; only events at or after this time
    """
    from app.services.device_log_bus import get_log_bus

    await websocket.accept()

    since_dt: datetime | None = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            await websocket.close(code=1003, reason="Invalid 'since' timestamp (use ISO format)")
            return

    try:
        async for entry in get_log_bus().subscribe_stream(
            device_id, level=level, source=source, since=since_dt
        ):
            await websocket.send_text(json.dumps(entry.as_dict()))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.get("/{device_id}/logs", response_model=list[DeviceLogEventPublic])
def get_device_logs_http(
    db: SessionDep,
    device_id: uuid.UUID,
    level: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[DeviceLogEventPublic]:
    """HTTP: return the most recent persisted log events for a device (no streaming).

    For live streaming use the WebSocket endpoint above.
    """
    _get_device_or_404(db, device_id)

    stmt = select(DeviceLogEvent).where(DeviceLogEvent.device_id == device_id)
    if level:
        stmt = stmt.where(DeviceLogEvent.level == level)
    if source:
        stmt = stmt.where(DeviceLogEvent.source == source)
    stmt = stmt.order_by(DeviceLogEvent.ts.desc()).limit(limit)  # type: ignore[arg-type]

    rows = db.exec(stmt).all()
    return [
        DeviceLogEventPublic(
            id=r.id,
            device_id=r.device_id,
            ts=r.ts,
            level=r.level,
            source=r.source,
            message=r.message,
            fields_json=r.fields_json,
        )
        for r in reversed(rows)  # chronological order
    ]
