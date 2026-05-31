import json
import uuid
from dataclasses import dataclass

import pytest
from unittest.mock import MagicMock, patch

from app.adapters.spi import CapabilityUnsupportedError


@dataclass
class FakeDevice:
    id: uuid.UUID = uuid.uuid4()
    screen_version: int = 0
    provider_ids_json: str = '{"adb_serial": "emulator-5554", "instance_id": "i-abc"}'


def test_get_adb_serial_from_provider_ids():
    from app.adapters.android.observation import _get_adb_serial
    device = FakeDevice(provider_ids_json='{"adb_serial": "emulator-5556"}')
    assert _get_adb_serial(device) == "emulator-5556"


def test_get_adb_serial_default():
    from app.adapters.android.observation import _get_adb_serial
    device = FakeDevice(provider_ids_json="{}")
    assert _get_adb_serial(device) == "emulator-5554"


@pytest.mark.asyncio
async def test_observe_unsupported_tier_raises():
    from app.adapters.android.observation import observe_android
    device = FakeDevice()
    with pytest.raises(CapabilityUnsupportedError):
        await observe_android(device, "vlm")


def test_dump_ax_tree_structure():
    import sys
    mock_u2 = MagicMock()
    mock_device = MagicMock()
    mock_device.dump_hierarchy.return_value = (
        '<?xml version="1.0"?>'
        '<hierarchy rotation="0">'
        '<node class="android.widget.TextView" text="Hello" resource-id="" '
        'content-desc="" bounds="[0,0][100,50]" clickable="false"/>'
        '</hierarchy>'
    )
    mock_u2.connect.return_value = mock_device
    sys.modules["uiautomator2"] = mock_u2
    from app.adapters.android.observation import _dump_ax_tree
    result = _dump_ax_tree("emulator-5554")
    assert "nodes" in result
