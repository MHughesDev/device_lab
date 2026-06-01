# services/device_session.py — interactive session attach/detach (Phase 09, task 09-14)
"""
Manages runtime display_mode toggle between headless and interactive without
re-provisioning. Attach starts a MediaSource+peer; detach tears it down.

MCP exposure (mcp_exposed) is a separate axis and is not affected by attach/detach.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from app.models import Device

log = logging.getLogger(__name__)

# device_id → StreamPeer for active interactive sessions (separate from negotiated stream sessions)
_interactive_peers: dict[str, object] = {}


async def attach(db: Session, device_id: uuid.UUID) -> dict:
    """Start an interactive session for a device; set display_mode=interactive.

    Returns an SDP offer that the client must answer via the /stream/negotiate endpoint.
    Idempotent: if already interactive, returns the existing session info.
    """
    device = db.get(Device, device_id)
    if not device:
        raise ValueError(f"Device {device_id} not found")
    if device.state != "ready":
        raise ValueError(f"Device is not ready (state={device.state})")

    key = str(device_id)
    if key in _interactive_peers:
        peer = _interactive_peers[key]
        return {"status": "already_interactive", "display_mode": "interactive"}

    from app.stream.peer import StreamPeer
    peer = StreamPeer(device=device)
    offer = await peer.create_offer()

    _interactive_peers[key] = peer

    device.display_mode = "interactive"
    db.add(device)
    db.commit()

    _emit_session_event(device_id, "attach")
    log.info("Device %s attached to interactive session", device_id)

    return {
        "status": "attached",
        "display_mode": "interactive",
        "sdp_offer": offer.sdp,
        "sdp_type": offer.type,
    }


async def detach(db: Session, device_id: uuid.UUID) -> dict:
    """Tear down the interactive session; set display_mode=headless.

    Does not reprovision. MCP exposure is unaffected.
    """
    key = str(device_id)
    peer = _interactive_peers.pop(key, None)
    if peer:
        await peer.close()

    device = db.get(Device, device_id)
    if device:
        device.display_mode = "headless"
        db.add(device)
        db.commit()

    _emit_session_event(device_id, "detach")
    log.info("Device %s detached from interactive session", device_id)
    return {"status": "detached", "display_mode": "headless"}


def get_interactive_peer(device_id: uuid.UUID):
    return _interactive_peers.get(str(device_id))


def _emit_session_event(device_id: uuid.UUID, event: str) -> None:
    try:
        from app.services.device_log_bus import get_log_bus
        get_log_bus().emit(
            str(device_id),
            level="info",
            source="stream",
            message=f"Interactive session {event}",
            fields={"event": event, "device_id": str(device_id)},
        )
    except Exception:
        pass
