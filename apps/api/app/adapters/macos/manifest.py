# adapters/macos/manifest.py — macOS manifest capture (Phase 10, task 10-08)
"""
Introspects a running macOS VM (vz or QEMU) and produces a DeviceManifest spec_json.

Capture via SSHChannel:
  - brew list --json=v2         (Homebrew packages)
  - mas list                    (Mac App Store apps, if mas is installed)

Apple-gated for direct vz host access; SSH path works everywhere.
"""
from __future__ import annotations

import json
import logging
import platform

log = logging.getLogger(__name__)


def _require_darwin(what: str) -> None:
    if platform.system() != "Darwin":
        raise RuntimeError(f"{what} requires macOS; hard-refused on {platform.system()}")


async def capture(device: object) -> dict:
    """Introspect the macOS VM and return a spec dict."""
    install_steps = []
    capture_warnings: list[str] = []

    brew_out, brew_err = await _run_shell(device, "brew list --json=v2 2>/dev/null")
    if brew_out is not None:
        pkgs = _parse_brew(brew_out)
        if pkgs:
            install_steps.append({"type": "brew", "packages": pkgs})
    else:
        capture_warnings.append(f"brew list failed: {brew_err}")

    mas_out, mas_err = await _run_shell(device, "mas list 2>/dev/null")
    if mas_out is not None:
        for line in mas_out.strip().splitlines():
            parts = line.split(None, 1)
            if parts and parts[0].isdigit():
                install_steps.append({"type": "mas_install", "app_id": int(parts[0])})
    else:
        capture_warnings.append("mas not installed or failed")

    spec = {
        "install_steps": install_steps,
        "env_vars": {},
        "startup_commands": [],
        "metadata": {"capture_source": "macos"},
    }
    if capture_warnings:
        spec["metadata"]["capture_warnings"] = capture_warnings
    return spec


async def _run_shell(device: object, command: str):
    try:
        from app.transport.channel import ChannelFactory
        device_id = str(getattr(device, "id", ""))
        channel = await ChannelFactory.get(device, device_id=device_id)
        result = await channel.exec(["bash", "-c", command])
        if result.get("exit_code", 1) == 0:
            return result.get("stdout", ""), None
        return None, result.get("stderr", "non-zero exit")
    except Exception as exc:
        return None, str(exc)


def _parse_brew(output: str) -> list[str]:
    try:
        data = json.loads(output)
        formulae = [f["name"] for f in data.get("formulae", []) if isinstance(f, dict)]
        casks = [f"--cask {c['token']}" for c in data.get("casks", []) if isinstance(c, dict)]
        return formulae + casks
    except Exception:
        return []
