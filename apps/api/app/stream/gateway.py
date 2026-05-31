"""
Stream gateway — manages per-device WebRTC peer connections.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlmodel import Session

from app.core.config import settings
from app.models import Device, StreamSession
from app.stream.peer import StreamPeer

_TOKEN_EXPIRE_MINUTES = 60
_peers: dict[str, StreamPeer] = {}


def _issue_token(device_id: uuid.UUID, session_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(device_id),
        "sid": str(session_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _verify_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


async def negotiate(db: Session, device_id: uuid.UUID, sdp_offer: str, client_id: str) -> tuple[StreamSession, str]:
    """Accept an SDP offer, create a peer, return session with answer."""
    device = db.get(Device, device_id)
    if not device or device.state != "ready":
        raise ValueError("Device not found or not ready")

    peer = StreamPeer()
    # For offer-based flow: set remote offer first, create answer
    from aiortc import RTCSessionDescription  # type: ignore
    remote = RTCSessionDescription(sdp=sdp_offer, type="offer")
    await peer.pc.setRemoteDescription(remote)

    # Add video track and data channel before answer
    from app.stream.peer import _BlankVideoTrack
    peer.pc.addTrack(_BlankVideoTrack())
    peer._input_channel = peer.pc.createDataChannel("input")

    answer = await peer.pc.createAnswer()
    await peer.pc.setLocalDescription(answer)

    now = datetime.now(UTC)
    stream_session = StreamSession(
        device_id=device_id,
        session_token="",   # filled after id is set
        status="active",
        client_id=client_id,
        created_at=now,
        expires_at=now + timedelta(minutes=_TOKEN_EXPIRE_MINUTES),
    )
    db.add(stream_session)
    db.commit()
    db.refresh(stream_session)

    token = _issue_token(device_id, stream_session.id)
    stream_session.session_token = token
    db.add(stream_session)
    db.commit()

    _peers[str(stream_session.id)] = peer
    return stream_session, peer.pc.localDescription.sdp  # type: ignore


async def reconnect(db: Session, device_id: uuid.UUID, session_token: str) -> StreamSession:
    """Verify token and return existing session metadata for renegotiation."""
    try:
        claims = _verify_token(session_token)
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid session token: {e}") from e

    if claims.get("sub") != str(device_id):
        raise ValueError("Token device_id mismatch")

    session_id = uuid.UUID(claims["sid"])
    session = db.get(StreamSession, session_id)
    if not session or session.status == "closed":
        raise ValueError("Session not found or closed")

    device = db.get(Device, device_id)
    if not device or device.state != "ready":
        raise ValueError("Device not ready")

    return session


async def close_session(db: Session, session_id: uuid.UUID) -> None:
    peer = _peers.pop(str(session_id), None)
    if peer:
        await peer.close()
    session = db.get(StreamSession, session_id)
    if session:
        session.status = "closed"
        db.add(session)
        db.commit()
