import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.browser.adapter import BrowserAdapter, _sessions
from app.adapters.browser.session import BrowserSession
from app.models import Device, DeviceTemplate


def _make_device() -> Device:
    return Device(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        family="browser",
        state="provisioning",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_template() -> DeviceTemplate:
    return DeviceTemplate(id=uuid.uuid4(), family="browser", name="browser-local")


class TestBrowserAdapter:
    @pytest.mark.asyncio
    async def test_provision_creates_session(self) -> None:
        with patch.object(BrowserSession, "create", new_callable=AsyncMock) as mock_create:
            session = BrowserSession(device_id="test")
            mock_create.return_value = session
            adapter = BrowserAdapter()
            device = _make_device()
            template = _make_template()
            session_id = await adapter.provision(device, template)
            assert session_id == session.session_id
            assert str(device.id) in _sessions

    @pytest.mark.asyncio
    async def test_terminate_closes_session(self) -> None:
        adapter = BrowserAdapter()
        device = _make_device()
        session = BrowserSession(device_id=str(device.id))
        session.close = AsyncMock()
        _sessions[str(device.id)] = session

        await adapter.terminate(device)
        session.close.assert_called_once()
        assert str(device.id) not in _sessions

    @pytest.mark.asyncio
    async def test_terminate_missing_session_is_noop(self) -> None:
        adapter = BrowserAdapter()
        device = _make_device()
        # no session registered — should not raise
        await adapter.terminate(device)

    def test_get_session_returns_session(self) -> None:
        adapter = BrowserAdapter()
        device = _make_device()
        session = BrowserSession(device_id=str(device.id))
        _sessions[str(device.id)] = session
        assert adapter.get_session(str(device.id)) is session
        del _sessions[str(device.id)]


def test_manifest_spi_version():
    from app.adapters.spi import SPI_VERSION
    assert BrowserAdapter.manifest().spi_version == SPI_VERSION


def test_manifest_family():
    assert BrowserAdapter.manifest().family == "browser"


def test_manifest_snapshot_not_capable():
    assert BrowserAdapter.manifest().capabilities.snapshot is False
