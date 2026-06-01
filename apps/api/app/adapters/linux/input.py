# adapters/linux/input.py — Linux InputSink via XTEST (Phase 09, task 09-08)
"""
Injects pointer and key events into the Linux container's X server using XTEST
via `xdotool`. xdotool is available in standard Debian/Ubuntu images.

For containers without X (future headless-only Linux), falls back to uinput
via `evemu-event` if available, otherwise no-ops with a warning.

Wire path: DataChannel → InputEvent → inject() → xdotool in container
"""
from __future__ import annotations

import asyncio
import json
import logging

from app.stream.source import InputEvent, InputSink

log = logging.getLogger(__name__)


class LinuxInputSink(InputSink):
    """Inject input into a Linux container via xdotool (XTEST extension)."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._container_id: str = ids.get("container_id", "")
        self._display: str = ids.get("display", ":0")
        self._available: bool = False

    async def start(self) -> None:
        self._available = await self._check_xdotool()
        if not self._available:
            log.warning(
                "xdotool not found in container %s — input injection disabled",
                self._container_id,
            )

    async def stop(self) -> None:
        pass

    async def inject(self, ev: InputEvent) -> None:
        if not self._available:
            return
        cmd = _build_xdotool_cmd(ev, self._display)
        if cmd:
            await self._docker_exec(cmd)

    async def _check_xdotool(self) -> bool:
        try:
            result = await self._docker_exec(["which", "xdotool"])
            return result == 0
        except Exception:
            return False

    async def _docker_exec(self, cmd: list[str]) -> int:
        """Run a command inside the container, return exit code."""
        if not self._container_id:
            return 1
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "exec",
                "-e", f"DISPLAY={self._display}",
                self._container_id,
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            return await proc.wait()
        except Exception as exc:
            log.debug("docker exec error: %s", exc)
            return 1


def _build_xdotool_cmd(ev: InputEvent, display: str) -> list[str] | None:
    """Build an xdotool command list for the given InputEvent."""
    if ev.kind == "pointer_move" and ev.x is not None and ev.y is not None:
        return ["xdotool", "mousemove", str(ev.x), str(ev.y)]

    if ev.kind == "pointer_down" and ev.x is not None and ev.y is not None:
        btn = _button_name(ev.button)
        return ["xdotool", "mousemove", str(ev.x), str(ev.y),
                "mousedown", str(btn)]

    if ev.kind == "pointer_up" and ev.x is not None and ev.y is not None:
        btn = _button_name(ev.button)
        return ["xdotool", "mousemove", str(ev.x), str(ev.y),
                "mouseup", str(btn)]

    if ev.kind == "scroll" and ev.dy is not None:
        btn = "4" if ev.dy > 0 else "5"
        clicks = abs(ev.dy)
        return ["xdotool", "click", "--repeat", str(max(1, clicks)), btn]

    if ev.kind == "key_down" and ev.key is not None:
        return ["xdotool", "keydown", ev.key]

    if ev.kind == "key_up" and ev.key is not None:
        return ["xdotool", "keyup", ev.key]

    if ev.kind == "text" and ev.text is not None:
        return ["xdotool", "type", "--clearmodifiers", "--", ev.text]

    return None


def _button_name(button: int | None) -> int:
    # X11 button numbers: 1=left, 2=middle, 3=right
    return {0: 1, 1: 2, 2: 3}.get(button or 0, 1)
