# adapters/macos/vz_provision.py — macOS VM via Virtualization.framework (Phase 09, task 09-11)
"""
Provisions macOS VMs on Apple Silicon using Apple's Virtualization.framework (vz).
Provides a real Metal-backed framebuffer (VZMacGraphicsDeviceConfiguration) vs the
QEMU VNC stop-gap added in Phase 08.

Architecture: Python control plane → typed Unix socket RPC → Swift sidecar process
  (vz-sidecar) that calls VZVirtualMachine. The sidecar is a thin, typed adapter;
  all policy and lifecycle remain in Python.

This provisioner is hard-refused on Intel/Linux hosts. The Phase 08 QEMU macOS path
remains available via provider_ids "vz": false or when not on Apple Silicon.

ADR: docs/design/adr/adr-0006-vz-macos-local.md
"""
from __future__ import annotations

import asyncio
import json
import logging
import platform
import struct
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

_SIDECAR_SOCKET_DIR = Path(tempfile.gettempdir()) / "devicelab-vz"
_SIDECAR_BINARY_NAME = "devicelab-vz-sidecar"

# Typed RPC message tags (single byte)
_RPC_PROVISION = 0x01
_RPC_START = 0x02
_RPC_STOP = 0x03
_RPC_SCREENSHOT = 0x04
_RPC_HID_EVENT = 0x05
_RPC_CAPTURE_START = 0x06
_RPC_CAPTURE_STOP = 0x07
_RPC_OK = 0x80
_RPC_ERR = 0x81


def is_apple_silicon() -> bool:
    """Return True only on Apple Silicon (arm64 Darwin)."""
    return platform.system() == "Darwin" and platform.machine() == "arm64"


class VzSidecarClient:
    """Typed RPC client for the vz sidecar process."""

    def __init__(self, socket_path: str) -> None:
        self._socket_path = socket_path
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_unix_connection(self._socket_path)

    async def close(self) -> None:
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass

    async def _call(self, tag: int, payload: bytes = b"") -> bytes:
        if self._writer is None:
            raise OSError("Sidecar not connected")
        # Frame: tag(1) + length(4) + payload
        frame = struct.pack(">BI", tag, len(payload)) + payload
        self._writer.write(frame)
        await self._writer.drain()
        # Response: tag(1) + length(4) + payload
        header = await self._reader.readexactly(5)
        resp_tag, resp_len = struct.unpack(">BI", header)
        resp_payload = await self._reader.readexactly(resp_len) if resp_len else b""
        if resp_tag == _RPC_ERR:
            raise RuntimeError(f"Sidecar error: {resp_payload.decode()}")
        return resp_payload

    async def provision(self, config: dict) -> dict:
        payload = json.dumps(config).encode()
        result = await self._call(_RPC_PROVISION, payload)
        return json.loads(result)

    async def start(self, vm_id: str) -> None:
        await self._call(_RPC_START, vm_id.encode())

    async def stop(self, vm_id: str) -> None:
        await self._call(_RPC_STOP, vm_id.encode())

    async def start_capture(self, vm_id: str, callback_port: int) -> None:
        payload = json.dumps({"vm_id": vm_id, "port": callback_port}).encode()
        await self._call(_RPC_CAPTURE_START, payload)

    async def stop_capture(self, vm_id: str) -> None:
        await self._call(_RPC_CAPTURE_STOP, vm_id.encode())

    async def send_hid(self, vm_id: str, event: dict) -> None:
        payload = json.dumps({"vm_id": vm_id, "event": event}).encode()
        await self._call(_RPC_HID_EVENT, payload)


class VzMacosProvisioner:
    """Provision a macOS VM via Virtualization.framework (Apple Silicon only)."""

    def __init__(self, device: object) -> None:
        self._device = device
        self._client: VzSidecarClient | None = None
        self._vm_id: str | None = None

    async def provision(self) -> dict:
        """Provision a macOS VM; returns provider_ids dict."""
        if not is_apple_silicon():
            raise RuntimeError(
                "VzMacosProvisioner requires Apple Silicon (arm64 Darwin); "
                "use QEMU macOS provisioner on this host."
            )

        socket_path = str(_SIDECAR_SOCKET_DIR / "sidecar.sock")
        self._client = VzSidecarClient(socket_path)
        try:
            await self._client.connect()
        except (OSError, FileNotFoundError) as exc:
            raise RuntimeError(
                f"vz sidecar not running at {socket_path}. "
                f"Start devicelab-vz-sidecar before provisioning macOS VMs. "
                f"Original error: {exc}"
            ) from exc

        config = {
            "cpu_count": getattr(self._device, "vcpu", 4),
            "memory_mb": getattr(self._device, "ram_mb", 8192),
            "disk_gb": 50,
            "display_width": 1920,
            "display_height": 1080,
        }
        result = await self._client.provision(config)
        self._vm_id = result["vm_id"]
        await self._client.start(self._vm_id)

        return {
            "vm_id": self._vm_id,
            "sidecar_socket": socket_path,
            "location": "local",
            "vz": True,
        }

    async def deprovision(self, provider_ids: dict) -> None:
        if not self._client or not self._vm_id:
            return
        try:
            await self._client.stop(self._vm_id)
        finally:
            await self._client.close()
