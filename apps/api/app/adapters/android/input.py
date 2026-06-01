# adapters/android/input.py — Android InputSink via scrcpy control protocol (Phase 09, task 09-06)
"""
Injects pointer/key/text via the scrcpy control socket (sub-frame latency).
Maps InputEvent → scrcpy control messages as described in scrcpy's ControlMsg.java.

Reference: https://github.com/Genymobile/scrcpy/blob/master/app/src/control_msg.h
"""
from __future__ import annotations

import asyncio
import json
import logging
import struct

from app.stream.source import InputEvent, InputSink

log = logging.getLogger(__name__)

_SCRCPY_CONTROL_PORT = 27184

# scrcpy control message types
_MSG_INJECT_TOUCH = 2
_MSG_INJECT_KEYCODE = 0
_MSG_INJECT_TEXT = 1
_MSG_INJECT_SCROLL = 3

# Android MotionEvent actions
_ACTION_DOWN = 0
_ACTION_UP = 1
_ACTION_MOVE = 2

# Pointer ID for our synthetic touch
_POINTER_ID = 0xFFFFFFFF


class AndroidInputSink(InputSink):
    """Inject input into an Android device via the scrcpy control socket."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._adb_serial: str = ids.get("adb_serial", "emulator-5554")
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._screen_width = 1080
        self._screen_height = 1920

    async def start(self) -> None:
        try:
            _, self._writer = await asyncio.open_connection("127.0.0.1", _SCRCPY_CONTROL_PORT)
            log.debug("Android scrcpy control socket connected")
        except OSError as exc:
            log.warning("Cannot connect to scrcpy control socket: %s — falling back to adb input", exc)
            self._writer = None

    async def stop(self) -> None:
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None

    async def inject(self, ev: InputEvent) -> None:
        if self._writer:
            await self._inject_via_control(ev)
        else:
            await self._inject_via_adb(ev)

    async def _inject_via_control(self, ev: InputEvent) -> None:
        """Inject event via scrcpy control socket (fast path)."""
        msg = _encode_control_message(ev, self._screen_width, self._screen_height)
        if msg is None:
            return
        async with self._lock:
            try:
                self._writer.write(msg)
                await self._writer.drain()
            except Exception as exc:
                log.debug("Control socket write failed: %s", exc)

    async def _inject_via_adb(self, ev: InputEvent) -> None:
        """Fallback: inject via adb shell input (slow; only for degraded mode)."""
        cmd: list[str] | None = None
        if ev.kind == "pointer_down" and ev.x is not None and ev.y is not None:
            cmd = ["adb", "-s", self._adb_serial, "shell", "input", "tap",
                   str(ev.x), str(ev.y)]
        elif ev.kind == "key_down" and ev.key is not None:
            cmd = ["adb", "-s", self._adb_serial, "shell", "input", "keyevent", ev.key]
        elif ev.kind == "text" and ev.text is not None:
            cmd = ["adb", "-s", self._adb_serial, "shell", "input", "text",
                   ev.text.replace(" ", "%s")]
        if cmd:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()


def _encode_control_message(ev: InputEvent, w: int, h: int) -> bytes | None:
    """Encode an InputEvent as a scrcpy control message byte string."""
    if ev.kind in ("pointer_move", "pointer_down", "pointer_up"):
        action = {
            "pointer_move": _ACTION_MOVE,
            "pointer_down": _ACTION_DOWN,
            "pointer_up": _ACTION_UP,
        }[ev.kind]
        x = int((ev.x or 0) * w / 1000) if (ev.x or 0) <= 1000 else (ev.x or 0)
        y = int((ev.y or 0) * h / 1000) if (ev.y or 0) <= 1000 else (ev.y or 0)
        pressure = 1.0 if ev.kind == "pointer_down" else (0.0 if ev.kind == "pointer_up" else 1.0)
        # struct: type(1) action(4) pointer_id(8) x(4) y(4) width(2) height(2) pressure(2) buttons(4)
        return struct.pack(">B i Q i i H H H i",
                           _MSG_INJECT_TOUCH, action, _POINTER_ID,
                           x, y, w, h, int(pressure * 0xFFFF), 0)
    if ev.kind == "scroll" and ev.x is not None and ev.y is not None:
        # struct: type(1) x(4) y(4) width(2) height(2) hscroll(4) vscroll(4) buttons(4)
        return struct.pack(">B i i H H i i i",
                           _MSG_INJECT_SCROLL,
                           ev.x, ev.y, w, h,
                           ev.dx or 0, ev.dy or 0, 0)
    if ev.kind == "key_down" and ev.key is not None:
        keycode = _android_keycode(ev.key)
        # struct: type(1) action(4) keycode(4) repeat(4) metastate(4)
        return struct.pack(">B i i i i", _MSG_INJECT_KEYCODE, _ACTION_DOWN, keycode, 0, 0)
    if ev.kind == "key_up" and ev.key is not None:
        keycode = _android_keycode(ev.key)
        return struct.pack(">B i i i i", _MSG_INJECT_KEYCODE, _ACTION_UP, keycode, 0, 0)
    if ev.kind == "text" and ev.text is not None:
        encoded = ev.text.encode("utf-8")
        # struct: type(1) length(4) text(N)
        return struct.pack(">B I", _MSG_INJECT_TEXT, len(encoded)) + encoded
    return None


def _android_keycode(key: str) -> int:
    """Map an XKB key name or keycode string to an Android keycode integer."""
    _MAP = {
        "Return": 66, "BackSpace": 67, "Tab": 61, "Escape": 111,
        "space": 62, "Delete": 112, "Home": 3, "End": 123,
        "Left": 21, "Right": 22, "Up": 19, "Down": 20,
        "VolumeUp": 24, "VolumeDown": 25, "Power": 26,
        "0": 7, "1": 8, "2": 9, "3": 10, "4": 11,
        "5": 12, "6": 13, "7": 14, "8": 15, "9": 16,
    }
    if key.isdigit():
        return int(key)
    return _MAP.get(key, 0)
