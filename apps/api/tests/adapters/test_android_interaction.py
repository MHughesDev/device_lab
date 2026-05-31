import sys
import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

# Inject mock uiautomator2 before importing interaction module
_mock_u2 = MagicMock()
sys.modules.setdefault("uiautomator2", _mock_u2)

from app.adapters.spi import CapabilityUnsupportedError


@dataclass
class FakeDevice:
    id: uuid.UUID = uuid.uuid4()
    provider_ids_json: str = '{"adb_serial": "emulator-5554"}'


@pytest.mark.asyncio
async def test_unsupported_action_raises():
    from app.adapters.android.interaction import act_android
    with pytest.raises(CapabilityUnsupportedError):
        await act_android(FakeDevice(), "navigate", {})


@pytest.mark.asyncio
async def test_click_calls_u2_click():
    import sys
    mock_d = MagicMock()
    mock_u2 = MagicMock()
    mock_u2.connect.return_value = mock_d
    sys.modules["uiautomator2"] = mock_u2
    from app.adapters.android.interaction import act_android
    await act_android(FakeDevice(), "click", {"x": 10, "y": 20})
    mock_d.click.assert_called_once_with(10, 20)


@pytest.mark.asyncio
async def test_type_calls_set_text():
    import sys
    mock_d = MagicMock()
    mock_u2 = MagicMock()
    mock_u2.connect.return_value = mock_d
    sys.modules["uiautomator2"] = mock_u2
    from app.adapters.android.interaction import act_android
    await act_android(FakeDevice(), "type", {"text": "hello"})
    mock_d(focused=True).set_text.assert_called_with("hello")


@pytest.mark.asyncio
async def test_key_calls_press():
    import sys
    mock_d = MagicMock()
    mock_u2 = MagicMock()
    mock_u2.connect.return_value = mock_d
    sys.modules["uiautomator2"] = mock_u2
    from app.adapters.android.interaction import act_android
    await act_android(FakeDevice(), "key", {"keycode": "home"})
    mock_d.press.assert_called_once_with("home")
