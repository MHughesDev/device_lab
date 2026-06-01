# adapters/android/local_provision.py — AVD lifecycle for local Android devices
from __future__ import annotations
import asyncio
import subprocess
import time
import uuid

_DEFAULT_SYSTEM_IMAGE = "system-images;android-34;google_apis;x86_64"
_ADB_WAIT_TIMEOUT_S = 300  # 5 min; mirrors cloud SSM bootstrap timeout


async def provision(device: object, template: object) -> dict:
    """Create and boot an AVD for a local Android device."""
    device_id = str(getattr(device, "id", uuid.uuid4()))
    avd_name = f"devicelab-{device_id[:8]}"

    system_image = _DEFAULT_SYSTEM_IMAGE
    extra = getattr(template, "extra_config", None)
    if isinstance(extra, dict):
        system_image = extra.get("system_image", _DEFAULT_SYSTEM_IMAGE)

    loop = asyncio.get_event_loop()

    await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            ["avdmanager", "create", "avd", "-n", avd_name, "-k", system_image, "--force"],
            capture_output=True,
        ),
    )

    # Popen is not blocking; emulator runs in the background
    subprocess.Popen(
        ["emulator", "-avd", avd_name, "-no-window", "-no-audio", "-no-snapshot", "-gpu", "off"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    adb_serial = await _wait_for_device(timeout_s=_ADB_WAIT_TIMEOUT_S)

    return {
        "avd_name": avd_name,
        "adb_serial": adb_serial,
        "system_image": system_image,
        "location": "local",
    }


async def terminate(device: object) -> None:
    """Shut down the emulator and delete the AVD. Idempotent."""
    import json
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial = ids.get("adb_serial")
    avd_name = ids.get("avd_name")

    loop = asyncio.get_event_loop()

    if adb_serial:
        await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["adb", "-s", adb_serial, "emu", "kill"], capture_output=True
            ),
        )
        await asyncio.sleep(2)

    if avd_name:
        await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["avdmanager", "delete", "avd", "-n", avd_name], capture_output=True
            ),
        )


async def _wait_for_device(timeout_s: int = 300) -> str:
    """Poll adb devices until an emulator serial appears. Returns the serial."""
    deadline = time.monotonic() + timeout_s
    loop = asyncio.get_event_loop()

    while time.monotonic() < deadline:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(["adb", "devices"], capture_output=True, text=True),
        )
        for line in result.stdout.splitlines():
            if line.startswith("emulator-") and "\tdevice" in line:
                return line.split("\t")[0]
        await asyncio.sleep(2)

    raise TimeoutError(f"No emulator appeared in adb within {timeout_s}s")
