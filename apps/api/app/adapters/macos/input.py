# adapters/macos/input.py — macOS InputSink via vz virtual HID (Phase 09, task 09-12)
"""
Injects input into a macOS VM via the vz sidecar's virtual HID path.
The sidecar drives VZVirtualMachine's virtual pointing device and keyboard,
which appear as real HID devices inside the guest.

On non-Apple hosts, or when the sidecar is unavailable, falls back to
NullInputSink behavior with a warning.
"""
from __future__ import annotations

import json
import logging

from app.stream.source import InputEvent, InputSink

log = logging.getLogger(__name__)


class MacosInputSink(InputSink):
    """Inject input into a macOS VM via vz sidecar virtual HID."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._vm_id: str = ids.get("vm_id", "")
        self._sidecar_socket: str = ids.get("sidecar_socket", "")
        self._client = None
        self._available = False

    async def start(self) -> None:
        if not self._vm_id or not self._sidecar_socket:
            log.warning("MacosInputSink: no vm_id/sidecar_socket — input injection disabled")
            return
        try:
            from app.adapters.macos.vz_provision import VzSidecarClient
            self._client = VzSidecarClient(self._sidecar_socket)
            await self._client.connect()
            self._available = True
            log.debug("macOS vz HID input connected")
        except Exception as exc:
            log.warning("Cannot connect to vz sidecar for input: %s", exc)

    async def stop(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        self._available = False

    async def inject(self, ev: InputEvent) -> None:
        if not self._available or not self._client:
            return
        hid_event = _to_vz_hid_event(ev)
        if hid_event:
            try:
                await self._client.send_hid(self._vm_id, hid_event)
            except Exception as exc:
                log.debug("vz HID send error: %s", exc)


def _to_vz_hid_event(ev: InputEvent) -> dict | None:
    """Convert an InputEvent to a vz sidecar HID event dict."""
    if ev.kind == "pointer_move" and ev.x is not None and ev.y is not None:
        return {"type": "pointer_move", "x": ev.x, "y": ev.y}

    if ev.kind == "pointer_down" and ev.x is not None and ev.y is not None:
        return {"type": "pointer_down", "x": ev.x, "y": ev.y,
                "button": ev.button or 0}

    if ev.kind == "pointer_up":
        return {"type": "pointer_up", "button": ev.button or 0}

    if ev.kind == "scroll" and ev.dx is not None and ev.dy is not None:
        return {"type": "scroll", "dx": ev.dx, "dy": ev.dy}

    if ev.kind == "key_down" and ev.key is not None:
        return {"type": "key_down", "key": ev.key}

    if ev.kind == "key_up" and ev.key is not None:
        return {"type": "key_up", "key": ev.key}

    if ev.kind == "text" and ev.text is not None:
        return {"type": "text", "text": ev.text}

    return None
