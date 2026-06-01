from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlmodel import Session

from app.adapters.browser.session import BrowserSession
from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    SPI_VERSION,
)
from app.models import Device, DeviceTemplate

_sessions: dict[str, BrowserSession] = {}


class BrowserAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="browser",
            display_name="Browser (Playwright)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["navigate", "click", "type", "fill_form",
                          "select_option", "scroll", "wait_for", "read_content"],
                network=[],
                streaming=False,
                snapshot=False,
                screen_recording=True,
            ),
            required_providers=["local_playwright"],
        )

    async def observe(self, device: object, tier: str) -> object:
        from app.adapters.spi import CapabilityUnsupportedError
        if tier not in self.manifest().capabilities.observe:
            raise CapabilityUnsupportedError(tier, "browser")
        from app.services.observation import observe_device
        return await observe_device(device, tier)

    async def act(self, device: object, action: str, params: dict) -> object:
        from app.adapters.spi import CapabilityUnsupportedError
        if action not in self.manifest().capabilities.interact:
            raise CapabilityUnsupportedError(action, "browser")
        from app.services.interaction import act_on_device
        return await act_on_device(device, action, params)
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
