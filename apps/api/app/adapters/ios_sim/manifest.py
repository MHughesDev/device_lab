# adapters/ios_sim/manifest.py — iOS Simulator manifest capture (Phase 10, task 10-08)
"""
Introspects an iOS Simulator and produces a DeviceManifest spec_json.

Capture via xcrun simctl:
  - xcrun simctl listapps {udid} — installed user app bundle IDs

Apple-gated: hard-refused on non-macOS hosts.
"""
from __future__ import annotations

import asyncio
import json
import logging
import platform

log = logging.getLogger(__name__)


async def capture(device: object) -> dict:
    """Introspect the iOS Simulator and return a spec dict."""
    if platform.system() != "Darwin":
        raise RuntimeError("iOS Simulator manifest capture requires macOS")

    ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    udid: str = ids.get("udid", "booted")

    install_steps = []
    capture_warnings: list[str] = []

    try:
        proc = await asyncio.create_subprocess_exec(
            "xcrun", "simctl", "listapps", udid,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        output = stdout.decode("utf-8", errors="replace")
        apps = _parse_listapps(output)
        for app in apps:
            install_steps.append({
                "type": "xcrun_install",
                "app_path": f"[reference: {app['bundle_id']}]",
                "bundle_id": app["bundle_id"],
            })
    except Exception as exc:
        capture_warnings.append(f"simctl listapps failed: {exc}")

    spec = {
        "install_steps": install_steps,
        "env_vars": {},
        "startup_commands": [],
        "metadata": {"capture_source": "ios_sim", "udid": udid},
    }
    if capture_warnings:
        spec["metadata"]["capture_warnings"] = capture_warnings
    return spec


def _parse_listapps(output: str) -> list[dict]:
    """Parse simctl listapps plist output (simplified; handles XML and dict text formats)."""
    apps = []
    try:
        import plistlib
        data = plistlib.loads(output.encode())
        for bundle_id, info in data.items():
            apps.append({"bundle_id": bundle_id, "name": info.get("CFBundleDisplayName", bundle_id)})
    except Exception:
        # Fallback: look for bundle ID patterns in text output
        import re
        for m in re.finditer(r'"?([\w.]+\.\w+)"?\s*=\s*\{', output):
            apps.append({"bundle_id": m.group(1), "name": m.group(1)})
    return apps
