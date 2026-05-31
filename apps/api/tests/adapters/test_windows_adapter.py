import pytest
from app.adapters.windows.adapter import WindowsAdapter
from app.adapters.spi import CapabilityUnsupportedError


def test_manifest_family():
    assert WindowsAdapter.manifest().family == "windows"


def test_manifest_snapshot_capable():
    assert WindowsAdapter.manifest().capabilities.snapshot is True


@pytest.mark.asyncio
async def test_unsupported_action_raises():
    from app.adapters.windows.interaction import act_windows
    import uuid
    from dataclasses import dataclass

    @dataclass
    class FakeDevice:
        id: uuid.UUID = uuid.uuid4()
        provider_ids_json: str = '{"instance_id": "i-win", "region": "us-east-1"}'

    with pytest.raises(CapabilityUnsupportedError):
        await act_windows(FakeDevice(), "navigate", {})
