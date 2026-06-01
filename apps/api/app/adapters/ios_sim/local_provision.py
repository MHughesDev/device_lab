# adapters/ios_sim/local_provision.py — xcrun simctl provisioner for local iOS Simulator
from __future__ import annotations
import asyncio
import re
import subprocess
import time

from app.services.local.host_probe import probe_host
from app.services.local.placement import PlacementError

_BOOT_WAIT_TIMEOUT_S = 120
_DEFAULT_DEVICE_TYPE = "iPhone 15"
_DEFAULT_RUNTIME = "iOS-17-0"


async def provision(device: object, template: object) -> dict:
    """Create and boot an iOS Simulator via xcrun simctl.

    Hard-refused on non-Apple hardware; requires Xcode and the target runtime.
    """
    caps = probe_host()
    if not caps.is_apple_hardware:
        raise PlacementError(
            "iOS Simulator local devices require Apple hardware with Xcode installed. "
            "Set placement_policy=cloud_only on non-Apple hosts."
        )

    extra = getattr(template, "extra_config", None) or {}
    device_type = extra.get("device_type", _DEFAULT_DEVICE_TYPE) if isinstance(extra, dict) else _DEFAULT_DEVICE_TYPE
    runtime = extra.get("runtime", _DEFAULT_RUNTIME) if isinstance(extra, dict) else _DEFAULT_RUNTIME

    loop = asyncio.get_event_loop()

    create_result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            ["xcrun", "simctl", "create", "devicelab-sim", device_type, runtime],
            capture_output=True,
            text=True,
        ),
    )
    udid = create_result.stdout.strip()
    if not re.match(r"[A-F0-9-]{36}", udid, re.IGNORECASE):
        raise RuntimeError(
            f"xcrun simctl create returned unexpected output: {udid!r}. "
            "Ensure Xcode and the requested runtime are installed."
        )

    await loop.run_in_executor(
        None,
        lambda: subprocess.run(["xcrun", "simctl", "boot", udid], capture_output=True),
    )

    await _wait_for_boot(udid, timeout_s=_BOOT_WAIT_TIMEOUT_S)

    return {
        "sim_udid": udid,
        "device_type": device_type,
        "runtime": runtime,
        "location": "local",
    }


async def terminate(device: object) -> None:
    """Shutdown and delete the simulator. Idempotent."""
    import json
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    udid = ids.get("sim_udid")
    if not udid:
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: subprocess.run(["xcrun", "simctl", "shutdown", udid], capture_output=True),
    )
    await loop.run_in_executor(
        None,
        lambda: subprocess.run(["xcrun", "simctl", "delete", udid], capture_output=True),
    )


async def _wait_for_boot(udid: str, timeout_s: int = 120) -> None:
    """Poll simctl list until the simulator reaches Booted state."""
    deadline = time.monotonic() + timeout_s
    loop = asyncio.get_event_loop()

    while time.monotonic() < deadline:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["xcrun", "simctl", "list", "devices", udid, "--json"],
                capture_output=True,
                text=True,
            ),
        )
        if '"state" : "Booted"' in result.stdout or '"state": "Booted"' in result.stdout:
            return
        await asyncio.sleep(2)

    raise TimeoutError(f"Simulator {udid} did not reach Booted state within {timeout_s}s")
