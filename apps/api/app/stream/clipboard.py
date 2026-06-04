"""Bidirectional clipboard relay for the WebRTC "clipboard" data channel — Phase 11 (11-08).

The browser sends {"direction":"host_to_device","text":"..."} and the server injects the text
into the device using the family-appropriate clipboard write mechanism.  Device-to-host polling
is currently Linux-only via xclip; other families extend as needed.
"""

from __future__ import annotations

import asyncio
import json
import logging

logger = logging.getLogger(__name__)

_REDACT_TOKENS = {"password", "secret", "key", "token", "credential"}


def _looks_secret(text: str) -> bool:
    lower = text.lower()
    return any(tok in lower for tok in _REDACT_TOKENS)


async def inject_host_to_device(family: str, device, text: str) -> None:
    """Write *text* to the device clipboard using the family's mechanism."""
    if not text:
        return
    if family == "linux":
        # xclip installed in standard DeviceLab Linux base image
        from app.adapters.channels.docker_exec import DockerExecChannel
        ch = DockerExecChannel(device)
        await ch.exec(["sh", "-c", f"echo -n {_shell_quote(text)} | xclip -selection clipboard"])
    elif family == "android":
        from app.adapters.channels.adb import AdbChannel
        ch = AdbChannel(device)
        await ch.exec(
            ["am", "broadcast", "-a", "clipper.set", "--es", "text", text],
        )
    elif family == "windows":
        from app.adapters.channels.ssh import SSHChannel
        ch = SSHChannel(device)
        await ch.exec(f"Set-Clipboard -Value '{text.replace(chr(39), chr(39)*2)}'")
    elif family == "macos":
        from app.adapters.channels.ssh import SSHChannel
        ch = SSHChannel(device)
        await ch.exec(f"echo -n {_shell_quote(text)} | pbcopy")
    # ios_sim: no clipboard injection mechanism; silently skip


async def poll_device_clipboard(family: str, device) -> str | None:
    """Read current device clipboard text.  Returns None if unavailable."""
    try:
        if family == "linux":
            from app.adapters.channels.docker_exec import DockerExecChannel
            ch = DockerExecChannel(device)
            result = await ch.exec(["xclip", "-selection", "clipboard", "-o"])
            return result.strip() or None
        elif family == "windows":
            from app.adapters.channels.ssh import SSHChannel
            ch = SSHChannel(device)
            result = await ch.exec("Get-Clipboard")
            return result.strip() or None
        elif family == "macos":
            from app.adapters.channels.ssh import SSHChannel
            ch = SSHChannel(device)
            result = await ch.exec("pbpaste")
            return result.strip() or None
    except Exception as e:
        logger.debug("clipboard poll failed for %s: %s", family, e)
    return None


def _shell_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"
