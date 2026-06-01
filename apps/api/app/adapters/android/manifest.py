# adapters/android/manifest.py — Android manifest capture (Phase 10, task 10-06)
"""
Introspects a running Android AVD/device and produces a DeviceManifest spec_json.

Capture:
  - User-installed APKs:  adb shell pm list packages -3 -f
  - Device settings:      adb shell settings list global
  - ADB serial + SDK info from provider_ids

System packages (pre-installed by AOSP) are excluded by default.
APK paths are stored as references (not bundled in the manifest).
"""
from __future__ import annotations

import asyncio
import json
import logging

log = logging.getLogger(__name__)


async def capture(device: object) -> dict:
    """Introspect the Android device and return a spec dict."""
    ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial: str = ids.get("adb_serial", "emulator-5554")

    results = await asyncio.gather(
        _adb_shell(adb_serial, "pm list packages -3 -f"),
        _adb_shell(adb_serial, "settings list global"),
        return_exceptions=True,
    )

    pkg_out, settings_out = results

    install_steps = []
    capture_warnings: list[str] = []

    if isinstance(pkg_out, str):
        packages = _parse_pm_packages(pkg_out)
        for pkg in packages:
            install_steps.append({
                "type": "adb_install",
                "apk_path": pkg["path"],
                "package": pkg["package"],
            })
    else:
        capture_warnings.append(f"pm list packages failed: {pkg_out}")

    settings: dict[str, str] = {}
    if isinstance(settings_out, str):
        settings = _parse_settings(settings_out)
    else:
        capture_warnings.append("adb settings list failed")

    spec = {
        "install_steps": install_steps,
        "env_vars": {},
        "android_settings": settings,
        "metadata": {
            "capture_source": "android",
            "adb_serial": adb_serial,
        },
    }
    if capture_warnings:
        spec["metadata"]["capture_warnings"] = capture_warnings
    return spec


async def _adb_shell(serial: str, command: str):
    try:
        proc = await asyncio.create_subprocess_exec(
            "adb", "-s", serial, "shell", command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        return stdout.decode("utf-8", errors="replace")
    except Exception as exc:
        return exc


def _parse_pm_packages(output: str) -> list[dict]:
    """Parse 'pm list packages -3 -f' output into package dicts."""
    packages = []
    for line in output.splitlines():
        # Format: package:/data/app/com.example.app-xxx=/com.example.app
        if not line.startswith("package:"):
            continue
        rest = line[len("package:"):]
        # Split on '=' from the right to get package name
        if "=" in rest:
            path, _, pkg = rest.rpartition("=")
        else:
            path, pkg = rest, rest
        packages.append({"path": path.strip(), "package": pkg.strip()})
    return packages


def _parse_settings(output: str) -> dict[str, str]:
    settings: dict[str, str] = {}
    for line in output.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            settings[key.strip()] = value.strip()
    return settings
