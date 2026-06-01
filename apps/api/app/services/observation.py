from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from app.models import Device, ObservationEnvelope
from app.services import screen_version as sv


async def observe(
    db: Session,
    device_id: uuid.UUID,
    tier: str = "ax",
    delta_from: int | None = None,
) -> ObservationEnvelope:
    device = db.get(Device, device_id)
    if not device:
        return ObservationEnvelope(
            device_id=str(device_id),
            screen_version=0,
            tier=tier,
            warnings=["Device not found"],
            observed_at=datetime.now(UTC),
        )

    current_version = sv.current_version(db, device_id)
    warnings: list[str] = []
    structured: dict | None = None

    if device.state != "ready":
        warnings.append(f"Device is '{device.state}' — observation may be stale")

    if tier == "ax":
        structured = await _observe_ax(device)
    elif tier == "screenshot":
        structured = None  # screenshot returned as artifact ref
    elif tier == "vlm":
        warnings.append("VLM tier requires dangerous_mode — returning screenshot instead")
        structured = None
        tier = "screenshot"

    # Increment screen version after observation
    new_version = sv.increment(db, device_id)

    return ObservationEnvelope(
        device_id=str(device_id),
        screen_version=new_version,
        tier=tier,
        structured=structured,
        delta_from_version=delta_from,
        warnings=warnings,
        observed_at=datetime.now(UTC),
    )


async def _observe_ax(device: Device) -> dict:
    if device.family == "linux":
        # On a real device: run linux_ax.py via SSM. In phase 03, stub.
        return {
            "type": "ax_tree",
            "family": "linux",
            "note": "AX extraction runs on remote instance via SSM in phase 03",
            "nodes": [],
        }
    return {"type": "ax_tree", "family": device.family, "nodes": []}
