"""
Screen version tracking — monotonic counter per device.
Stored in the DB on the Device record (screen_version column added in phase 03 migration).
On conflict: raise ScreenVersionConflict.
"""
from __future__ import annotations

import uuid

from sqlmodel import Session

from app.models import Device


class ScreenVersionConflict(Exception):
    def __init__(self, device_id: str, expected: int, actual: int) -> None:
        super().__init__(f"Screen version conflict on {device_id}: expected {expected}, got {actual}")
        self.device_id = device_id
        self.expected = expected
        self.actual = actual


def current_version(db: Session, device_id: uuid.UUID) -> int:
    device = db.get(Device, device_id)
    if not device:
        return 0
    return getattr(device, "screen_version", 0) or 0


def increment(db: Session, device_id: uuid.UUID) -> int:
    device = db.get(Device, device_id)
    if not device:
        return 0
    current = getattr(device, "screen_version", 0) or 0
    new_version = current + 1
    device.screen_version = new_version  # type: ignore[attr-defined]
    db.add(device)
    db.commit()
    return new_version


def assert_version(db: Session, device_id: uuid.UUID, expected: int) -> None:
    actual = current_version(db, device_id)
    if actual != expected:
        raise ScreenVersionConflict(str(device_id), expected, actual)
