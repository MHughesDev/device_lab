# proxy.py — mitmproxy-based network capture addon for DeviceLab sessions
from __future__ import annotations
import asyncio
import uuid
from typing import Any

try:
    import mitmproxy.http  # type: ignore[import]
    from mitmproxy.options import Options  # type: ignore[import]
    from mitmproxy.tools.dump import DumpMaster  # type: ignore[import]
    _MITMPROXY_AVAILABLE = True
except ImportError:
    _MITMPROXY_AVAILABLE = False


class DeviceLabAddon:
    """mitmproxy addon — tags flows with device context and applies policy."""

    def __init__(self, device_id: uuid.UUID, session_id: str, capture: bool = True):
        self.device_id = device_id
        self.session_id = session_id
        self.capture = capture
        self.captured_flows: list[dict] = []

    def request(self, flow: Any) -> None:
        """Tag outbound request with device/session context."""
        if hasattr(flow, "request"):
            flow.request.headers["X-DeviceLab-Device"] = str(self.device_id)
            flow.request.headers["X-DeviceLab-Session"] = self.session_id

    def response(self, flow: Any) -> None:
        """Capture response if enabled."""
        if not self.capture:
            return
        entry: dict = {}
        if hasattr(flow, "request"):
            entry["url"] = str(flow.request.pretty_url) if hasattr(flow.request, "pretty_url") else ""
            entry["method"] = flow.request.method
        if hasattr(flow, "response") and flow.response is not None:
            entry["status_code"] = flow.response.status_code
        self.captured_flows.append(entry)


class NetworkProxy:
    def __init__(self, device_id: uuid.UUID, session_id: str, port: int = 8080):
        self.device_id = device_id
        self.session_id = session_id
        self.port = port
        self._master: Any = None
        self._addon: DeviceLabAddon | None = None

    async def start(self) -> None:
        """Start the mitmproxy DumpMaster in a background thread."""
        if not _MITMPROXY_AVAILABLE:
            raise RuntimeError("mitmproxy not installed — pip install mitmproxy")
        self._addon = DeviceLabAddon(self.device_id, self.session_id)
        opts = Options(listen_host="127.0.0.1", listen_port=self.port)
        self._master = DumpMaster(opts)
        self._master.addons.add(self._addon)
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._master.run)

    async def stop(self) -> None:
        """Shut down the proxy master cleanly."""
        if self._master is not None:
            self._master.shutdown()
            self._master = None

    def get_captured_flows(self) -> list[dict]:
        return self._addon.captured_flows if self._addon else []


def is_available() -> bool:
    return _MITMPROXY_AVAILABLE
