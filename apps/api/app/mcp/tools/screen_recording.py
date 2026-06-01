"""MCP tools for screen recording — start, stop, status, list."""
from __future__ import annotations

from app.mcp.gateway import mcp


@mcp.tool()
def start_recording(device_id: str) -> dict:
    """
    Start a screen recording on a device.

    Returns recording_id to pass to stop_recording. Only one recording is
    allowed per device at a time. Supported families: linux, macos, windows,
    android, ios_sim, ios_real, browser.
    """
    import asyncio
    import uuid
    from app.core.db import engine
    from sqlmodel import Session, select
    from app.models import Device, Workspace
    from app.services.screen_recording import start_recording as _start
    from app.mcp.capabilities import get_capabilities

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"success": False, "error": "Invalid device_id"}

        device = db.get(Device, did)
        if not device:
            return {"success": False, "error": "Device not found"}

        caps = get_capabilities(device.family)
        if not caps.screen_recording.supported:
            return {"success": False, "error": f"Screen recording not supported for family '{device.family}'"}

        if device.state != "ready":
            return {"success": False, "error": f"Device must be in 'ready' state (current: {device.state})"}

        try:
            session = asyncio.get_event_loop().run_until_complete(_start(device))
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            return {"success": False, "error": f"Recording start failed: {exc}"}

        result = {
            "success": True,
            "recording_id": session.recording_id,
            "device_id": device_id,
            "family": device.family,
            "started_at": session.started_at.isoformat(),
            "status": session.status,
        }
        if caps.screen_recording.max_duration_seconds:
            result["max_duration_seconds"] = caps.screen_recording.max_duration_seconds
        return result


@mcp.tool()
def stop_recording(device_id: str) -> dict:
    """
    Stop the active screen recording on a device.

    Returns artifact_id and storage_path. Call get_recording_artifact to
    get a download URL.
    """
    import asyncio
    import uuid
    from app.core.db import engine
    from sqlmodel import Session, select
    from app.models import Device, Workspace
    from app.services.screen_recording import stop_recording as _stop, get_status

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"success": False, "error": "Invalid device_id"}

        device = db.get(Device, did)
        if not device:
            return {"success": False, "error": "Device not found"}

        current = get_status(device_id)
        if not current:
            return {"success": False, "error": "No active recording for this device"}

        ws = db.exec(select(Workspace).limit(1)).first()
        if not ws:
            return {"success": False, "error": "Workspace not initialised"}

        try:
            session = asyncio.get_event_loop().run_until_complete(
                _stop(db, device, ws.id)
            )
        except Exception as exc:
            return {"success": False, "error": f"Recording stop failed: {exc}"}

        return {
            "success": session.status == "stopped",
            "recording_id": session.recording_id,
            "device_id": device_id,
            "status": session.status,
            "storage_path": session.storage_path,
            "artifact_id": session.artifact_id,
            "error": session.error,
        }


@mcp.tool()
def get_recording_status(device_id: str) -> dict:
    """Return the current recording state for a device."""
    from app.services.screen_recording import get_status
    from app.mcp.capabilities import get_capabilities
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device
    import uuid

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}

        device = db.get(Device, did)
        if not device:
            return {"error": "Device not found"}

        caps = get_capabilities(device.family)
        session = get_status(device_id)
        if not session:
            return {
                "device_id": device_id,
                "family": device.family,
                "recording": False,
                "screen_recording_supported": caps.screen_recording.supported,
                "output_format": caps.screen_recording.output_format,
                "max_duration_seconds": caps.screen_recording.max_duration_seconds,
            }

        return {
            "device_id": device_id,
            "family": device.family,
            "recording": True,
            "recording_id": session.recording_id,
            "started_at": session.started_at.isoformat(),
            "status": session.status,
            "screen_recording_supported": caps.screen_recording.supported,
            "output_format": caps.screen_recording.output_format,
            "max_duration_seconds": caps.screen_recording.max_duration_seconds,
        }


@mcp.tool()
def get_recording_artifact(artifact_id: str, expires_in_seconds: int = 3600) -> dict:
    """
    Get a download URL for a completed screen recording artifact.

    expires_in_seconds controls pre-signed URL lifetime for S3-backed artifacts.
    """
    import uuid
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Artifact
    from app.services.artifacts import get_presigned_download_url

    with Session(engine) as db:
        try:
            aid = uuid.UUID(artifact_id)
        except ValueError:
            return {"error": "Invalid artifact_id"}

        artifact = db.get(Artifact, aid)
        if not artifact:
            return {"error": "Artifact not found"}
        if artifact.artifact_type != "screen_recording":
            return {"error": "Artifact is not a screen recording"}
        if artifact.purged:
            return {"error": "Artifact has been purged"}

        url = get_presigned_download_url(artifact, expires_in_seconds=expires_in_seconds)
        return {
            "artifact_id": artifact_id,
            "download_url": url,
            "content_type": artifact.content_type,
            "size_bytes": artifact.size_bytes,
            "captured_at": artifact.captured_at.isoformat(),
            "purge_after": artifact.purge_after.isoformat(),
        }
