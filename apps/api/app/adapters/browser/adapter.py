from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlmodel import Session

from app.adapters.browser.session import BrowserSession
from app.models import Device, DeviceTemplate

_sessions: dict[str, BrowserSession] = {}


class BrowserAdapter:
    async def provision(self, device: Device, template: DeviceTemplate) -> str:
        session = await BrowserSession.create(device_id=str(device.id))
        _sessions[str(device.id)] = session
        return session.session_id

    async def terminate(self, device: Device) -> None:
        session = _sessions.pop(str(device.id), None)
        if session:
            await session.close()

    def get_session(self, device_id: str) -> BrowserSession | None:
        return _sessions.get(device_id)
