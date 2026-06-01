# adapters/windows/input.py — Windows InputSink via QEMU QMP (Phase 09, task 09-10)
"""
Injects pointer and key events into a QEMU Windows VM using the QEMU Machine
Protocol (QMP) over a Unix socket or TCP connection.

QMP commands used:
  - input-send-event  (QEMU >= 2.6) for keyboard and pointer events
  - mouse-button-event for button press/release

The QEMU process is started by the Phase 08 provisioner with:
  -qmp unix:/tmp/qmp-<container_id>.sock,server=on,wait=off

Reference: https://www.qemu.org/docs/master/interop/qmp-spec.html
"""
from __future__ import annotations

import asyncio
import json
import logging

from app.stream.source import InputEvent, InputSink

log = logging.getLogger(__name__)


class WindowsInputSink(InputSink):
    """Inject input into a Windows QEMU VM via QMP socket."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._container_id: str = ids.get("container_id", "")
        # QMP socket path set by provisioner; fall back to convention
        self._qmp_path: str = ids.get(
            "qmp_socket", f"/tmp/qmp-{self._container_id}.sock"
        )
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._connected = False

    async def start(self) -> None:
        try:
            self._reader, self._writer = await asyncio.open_unix_connection(self._qmp_path)
            # QMP sends a greeting; consume and send capabilities
            greeting = await self._reader.readline()
            log.debug("QMP greeting: %s", greeting.decode().strip())
            await self._send({"execute": "qmp_capabilities"})
            self._connected = True
            log.debug("QMP connected: %s", self._qmp_path)
        except (OSError, FileNotFoundError) as exc:
            log.warning("Cannot connect to QMP socket %s: %s — input injection disabled", self._qmp_path, exc)

    async def stop(self) -> None:
        self._connected = False
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None

    async def inject(self, ev: InputEvent) -> None:
        if not self._connected or self._writer is None:
            return
        events = _build_qmp_events(ev)
        for qmp_event in events:
            await self._send(qmp_event)

    async def _send(self, obj: dict) -> None:
        if self._writer is None:
            return
        async with self._lock:
            try:
                self._writer.write(json.dumps(obj).encode() + b"\n")
                await self._writer.drain()
                # Consume response line (fire-and-forget; we don't need the result)
                if self._reader:
                    await asyncio.wait_for(self._reader.readline(), timeout=0.5)
            except Exception as exc:
                log.debug("QMP send error: %s", exc)
                self._connected = False


def _build_qmp_events(ev: InputEvent) -> list[dict]:
    """Build QMP input-send-event command(s) for an InputEvent."""
    if ev.kind == "pointer_move" and ev.x is not None and ev.y is not None:
        return [_qmp_abs_pointer(ev.x, ev.y)]

    if ev.kind == "pointer_down" and ev.x is not None and ev.y is not None:
        btn = _qmp_button(ev.button)
        return [
            _qmp_abs_pointer(ev.x, ev.y),
            _qmp_button_event(btn, down=True),
        ]

    if ev.kind == "pointer_up":
        btn = _qmp_button(ev.button)
        return [_qmp_button_event(btn, down=False)]

    if ev.kind == "scroll" and ev.dy is not None:
        direction = "up" if ev.dy > 0 else "down"
        clicks = abs(ev.dy)
        result = []
        for _ in range(max(1, clicks)):
            result.append(_qmp_button_event(direction, down=True))
            result.append(_qmp_button_event(direction, down=False))
        return result

    if ev.kind == "key_down" and ev.key is not None:
        qcode = _qcode(ev.key)
        return [{"execute": "input-send-event", "arguments": {
            "events": [{"type": "key", "data": {"down": True, "key": {"type": "qcode", "data": qcode}}}]
        }}]

    if ev.kind == "key_up" and ev.key is not None:
        qcode = _qcode(ev.key)
        return [{"execute": "input-send-event", "arguments": {
            "events": [{"type": "key", "data": {"down": False, "key": {"type": "qcode", "data": qcode}}}]
        }}]

    return []


def _qmp_abs_pointer(x: int, y: int) -> dict:
    # QMP absolute pointer values are 0–32767
    ax = int(x * 32767 / 1000) if x <= 1000 else x
    ay = int(y * 32767 / 1000) if y <= 1000 else y
    return {"execute": "input-send-event", "arguments": {
        "events": [
            {"type": "abs", "data": {"axis": "x", "value": ax}},
            {"type": "abs", "data": {"axis": "y", "value": ay}},
        ]
    }}


def _qmp_button_event(button: str, *, down: bool) -> dict:
    return {"execute": "input-send-event", "arguments": {
        "events": [{"type": "btn", "data": {"down": down, "button": button}}]
    }}


def _qmp_button(button: int | None) -> str:
    return {0: "left", 1: "middle", 2: "right"}.get(button or 0, "left")


def _qcode(key: str) -> str:
    """Map XKB key name to QEMU qcode string."""
    _MAP = {
        "Return": "ret", "BackSpace": "backspace", "Tab": "tab",
        "Escape": "esc", "space": "spc", "Delete": "delete",
        "Home": "home", "End": "end", "Left": "left", "Right": "right",
        "Up": "up", "Down": "down", "F1": "f1", "F2": "f2",
        "F3": "f3", "F4": "f4", "F5": "f5", "F6": "f6",
        "F7": "f7", "F8": "f8", "F9": "f9", "F10": "f10",
        "F11": "f11", "F12": "f12",
        "shift_l": "shift", "shift_r": "shift",
        "control_l": "ctrl", "control_r": "ctrl",
        "alt_l": "alt", "alt_r": "alt",
    }
    return _MAP.get(key, key.lower())
