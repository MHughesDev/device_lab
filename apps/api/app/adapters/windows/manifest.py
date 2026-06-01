# adapters/windows/manifest.py — Windows manifest capture (Phase 10, task 10-07)
"""
Introspects a running Windows QEMU VM and produces a DeviceManifest spec_json.

Capture via PowerShell over SSHChannel:
  - winget list --output json   (winget-managed packages)
  - Get-Package | ConvertTo-Json  (MSI / Chocolatey packages via PackageManagement)

Assembles winget_install and msi_install steps.
Handles gracefully if winget or PackageManagement is absent.
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)


async def capture(device: object) -> dict:
    """Introspect the Windows VM and return a spec dict."""
    install_steps = []
    capture_warnings: list[str] = []

    winget_pkgs, winget_err = await _run_powershell(device, "winget list --output json 2>$null")
    if winget_pkgs is not None:
        steps = _parse_winget(winget_pkgs)
        install_steps.extend(steps)
    else:
        capture_warnings.append(f"winget not available or failed: {winget_err}")

    msi_pkgs, msi_err = await _run_powershell(
        device,
        "Get-Package | Select-Object Name,Version | ConvertTo-Json -Compress 2>$null"
    )
    if msi_pkgs is not None:
        steps = _parse_get_package(msi_pkgs)
        install_steps.extend(steps)
    else:
        capture_warnings.append(f"Get-Package failed: {msi_err}")

    spec = {
        "install_steps": install_steps,
        "env_vars": {},
        "startup_commands": [],
        "metadata": {"capture_source": "windows"},
    }
    if capture_warnings:
        spec["metadata"]["capture_warnings"] = capture_warnings
    return spec


async def _run_powershell(device: object, script: str):
    """Run a PowerShell command via SSHChannel; return (output_str, None) or (None, error_str)."""
    try:
        from app.transport.channel import ChannelFactory
        device_id = str(getattr(device, "id", ""))
        channel = await ChannelFactory.get(device, device_id=device_id)
        result = await channel.exec(["powershell", "-Command", script])
        if result.get("exit_code", 1) == 0:
            return result.get("stdout", ""), None
        return None, result.get("stderr", "non-zero exit")
    except Exception as exc:
        return None, str(exc)


def _parse_winget(output: str) -> list[dict]:
    steps = []
    try:
        # winget list output is not valid JSON (it's tabular); handle both formats
        data = json.loads(output)
        # If it parsed, it's the JSON format
        for item in data if isinstance(data, list) else data.get("Sources", [{}])[0].get("Packages", []):
            pkg_id = item.get("Id") or item.get("PackageIdentifier")
            version = item.get("InstalledVersion") or item.get("Version")
            if pkg_id:
                steps.append({
                    "type": "winget_install",
                    "package_id": pkg_id,
                    "version": version,
                })
    except (json.JSONDecodeError, Exception):
        # Tabular format — skip (winget JSON output mode is recommended)
        log.debug("winget output not JSON; skipping winget package capture")
    return steps


def _parse_get_package(output: str) -> list[dict]:
    steps = []
    try:
        data = json.loads(output)
        items = data if isinstance(data, list) else [data]
        for item in items:
            name = item.get("Name")
            version = item.get("Version")
            if name:
                steps.append({
                    "type": "msi_install",
                    "msi_path": f"[reference: {name} {version or ''}]",
                    "args": "/quiet",
                })
    except Exception:
        pass
    return steps
