# screen_recording.py — Recording state manager and per-family dispatcher
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

RecordingStatus = Literal["recording", "stopped", "failed"]


@dataclass
class RecordingSession:
    recording_id: str
    device_id: str
    family: str
    started_at: datetime
    status: RecordingStatus
    remote_handle: str | None = None  # PID or process handle on device
    storage_path: str | None = None   # set when stopped and uploaded
    artifact_id: str | None = None    # DB Artifact.id
    error: str | None = None


# Module-level state — one active recording per device at a time
_active: dict[str, RecordingSession] = {}


async def start_recording(device: object) -> RecordingSession:
    """Start screen recording on a device. Raises if one is already in progress."""
    device_id = str(device.id)  # type: ignore[attr-defined]
    family = device.family  # type: ignore[attr-defined]

    if device_id in _active:
        existing = _active[device_id]
        if existing.status == "recording":
            raise ValueError(f"Recording {existing.recording_id} already active on device {device_id}")

    recording_id = str(uuid.uuid4())
    session = RecordingSession(
        recording_id=recording_id,
        device_id=device_id,
        family=family,
        started_at=datetime.now(UTC),
        status="recording",
    )

    handle = await _dispatch_start(device, recording_id)
    session.remote_handle = handle
    _active[device_id] = session
    return session


async def stop_recording(db: object, device: object, workspace_id: uuid.UUID) -> RecordingSession:
    """Stop the active recording, upload artifact, return updated session."""
    device_id = str(device.id)  # type: ignore[attr-defined]
    session = _active.get(device_id)
    if not session or session.status != "recording":
        raise ValueError(f"No active recording for device {device_id}")

    try:
        storage_path = await _dispatch_stop(device, session)
        session.status = "stopped"
        session.storage_path = storage_path

        if storage_path:
            from app.services.artifacts import store_artifact
            from sqlmodel import Session as DBSession
            artifact = store_artifact(
                db=db,  # type: ignore[arg-type]
                workspace_id=workspace_id,
                artifact_type="screen_recording",
                storage_path=storage_path,
                content_type="video/mp4",
                size_bytes=0,
                retention_days=30,
            )
            session.artifact_id = str(artifact.id)
    except Exception as exc:
        session.status = "failed"
        session.error = str(exc)

    _active.pop(device_id, None)
    return session


def get_status(device_id: str) -> RecordingSession | None:
    return _active.get(device_id)


# ---------------------------------------------------------------------------
# Per-family dispatch
# ---------------------------------------------------------------------------

async def _dispatch_start(device: object, recording_id: str) -> str | None:
    family = device.family  # type: ignore[attr-defined]
    if family == "linux":
        from app.adapters.linux.recording import start as _start
    elif family == "macos":
        from app.adapters.macos.recording import start as _start  # type: ignore[no-redef]
    elif family == "windows":
        from app.adapters.windows.recording import start as _start  # type: ignore[no-redef]
    elif family == "android":
        from app.adapters.android.recording import start as _start  # type: ignore[no-redef]
    elif family == "ios_sim":
        from app.adapters.ios_sim.recording import start as _start  # type: ignore[no-redef]
    elif family == "browser":
        from app.adapters.browser.recording import start as _start  # type: ignore[no-redef]
    else:
        raise ValueError(f"Screen recording not supported for family '{family}'")
    return await _start(device, recording_id)


async def _dispatch_stop(device: object, session: RecordingSession) -> str | None:
    family = device.family  # type: ignore[attr-defined]
    if family == "linux":
        from app.adapters.linux.recording import stop as _stop
    elif family == "macos":
        from app.adapters.macos.recording import stop as _stop  # type: ignore[no-redef]
    elif family == "windows":
        from app.adapters.windows.recording import stop as _stop  # type: ignore[no-redef]
    elif family == "android":
        from app.adapters.android.recording import stop as _stop  # type: ignore[no-redef]
    elif family == "ios_sim":
        from app.adapters.ios_sim.recording import stop as _stop  # type: ignore[no-redef]
    elif family == "browser":
        from app.adapters.browser.recording import stop as _stop  # type: ignore[no-redef]
    else:
        raise ValueError(f"Screen recording not supported for family '{family}'")
    return await _stop(device, session)
