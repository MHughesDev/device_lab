# test_device_model_phase08.py — tests for Phase 08 four-axis device model (08-01, 08-02)
import uuid
from datetime import UTC, datetime

from app.models import Device, DeviceCreate, DevicePublic


def _make_device(**kwargs) -> Device:
    defaults = dict(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        family="linux",
        state="requested",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return Device(**defaults)


class TestDeviceDefaults:
    def test_device_defaults_headless_mcp_on(self) -> None:
        device = _make_device()
        assert device.display_mode == "headless"
        assert device.mcp_exposed is True
        assert device.name is None

    def test_device_accepts_name(self) -> None:
        device = _make_device(name="my-test-device")
        assert device.name == "my-test-device"

    def test_device_accepts_interactive_display_mode(self) -> None:
        device = _make_device(display_mode="interactive")
        assert device.display_mode == "interactive"

    def test_device_accepts_mcp_off(self) -> None:
        device = _make_device(mcp_exposed=False)
        assert device.mcp_exposed is False


class TestDeviceCreate:
    def test_create_device_accepts_four_axes(self) -> None:
        body = DeviceCreate(
            template_id=uuid.uuid4(),
            name="test-device",
            location="local",
            display_mode="interactive",
            mcp_exposed=False,
        )
        assert body.name == "test-device"
        assert body.location == "local"
        assert body.display_mode == "interactive"
        assert body.mcp_exposed is False

    def test_create_device_defaults(self) -> None:
        body = DeviceCreate(template_id=uuid.uuid4())
        assert body.location == "local"
        assert body.display_mode == "headless"
        assert body.mcp_exposed is True
        assert body.name is None


class TestDevicePublicTitle:
    def test_device_public_title_uses_name_when_set(self) -> None:
        did = uuid.uuid4()
        pub = DevicePublic(
            id=did,
            family="linux",
            location="local",
            name="my-named-device",
            display_mode="headless",
            mcp_exposed=True,
            state="ready",
            phase=None,
            cost_estimate=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert pub.title == "my-named-device"

    def test_device_public_title_falls_back(self) -> None:
        did = uuid.uuid4()
        pub = DevicePublic(
            id=did,
            family="android",
            location="local",
            name=None,
            display_mode="headless",
            mcp_exposed=True,
            state="ready",
            phase=None,
            cost_estimate=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert pub.title == f"android · {str(did)[:8]}"
