import uuid
from unittest.mock import patch

import pytest

from app.adapters.network.proxy import DeviceLabAddon, NetworkProxy, is_available


def test_is_available_returns_bool():
    result = is_available()
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_proxy_unavailable_raises():
    proxy = NetworkProxy(device_id=uuid.uuid4(), session_id="sess-1")
    with patch("app.adapters.network.proxy._MITMPROXY_AVAILABLE", False):
        with pytest.raises(RuntimeError, match="mitmproxy not installed"):
            await proxy.start()


def test_addon_captures_flow():
    addon = DeviceLabAddon(device_id=uuid.uuid4(), session_id="sess-cap", capture=True)

    class FakeRequest:
        pretty_url = "http://example.com"
        method = "GET"
        headers = {}

    class FakeResponse:
        status_code = 200

    class FakeFlow:
        request = FakeRequest()
        response = FakeResponse()

    addon.response(FakeFlow())
    assert len(addon.captured_flows) == 1


def test_addon_skips_capture():
    addon = DeviceLabAddon(device_id=uuid.uuid4(), session_id="sess-skip", capture=False)

    class FakeRequest:
        pretty_url = "http://example.com"
        method = "GET"
        headers = {}

    class FakeResponse:
        status_code = 200

    class FakeFlow:
        request = FakeRequest()
        response = FakeResponse()

    addon.response(FakeFlow())
    assert addon.captured_flows == []
