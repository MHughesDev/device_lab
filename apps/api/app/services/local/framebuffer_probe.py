# framebuffer_probe.py — per-family "is the screen capturable?" probe (Phase 08)
from __future__ import annotations
import json
import logging
import subprocess

log = logging.getLogger(__name__)

_TIMEOUT_S = 5  # must stay sub-second in practice; 5s is a generous ceiling


def probe(device: object) -> tuple[bool, str]:
    """Return (ok, message).

    ok=True  → framebuffer is present and a non-empty frame is capturable.
    ok=False → framebuffer unavailable; message is actionable.

    Each family check is fast (subprocess with a tight timeout). Failures are
    non-fatal to the caller — it decides whether to transition to failed or warn.
    """
    family: str = getattr(device, "family", "")
    ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")

    if family == "linux":
        return _probe_linux(ids)
    if family == "android":
        return _probe_android(ids)
    if family in ("windows", "macos"):
        return _probe_qemu_vnc(ids, family)
    if family == "ios_sim":
        return _probe_ios_sim(ids)
    return False, f"Unknown family '{family}'; cannot verify framebuffer"


def _probe_linux(ids: dict) -> tuple[bool, str]:
    container_id = ids.get("container_id", "")
    if not container_id:
        return False, "No container_id in provider_ids — container not provisioned"
    try:
        import docker
        client = docker.from_env()
        container = client.containers.get(container_id)
        # Check DISPLAY is set and Xvfb responds to xdpyinfo
        result = container.exec_run(
            "sh -c 'export DISPLAY=:0; xdpyinfo >/dev/null 2>&1 && echo ok || echo fail'",
            demux=False,
        )
        output = (result.output or b"").decode(errors="replace").strip()
        if "ok" in output:
            return True, "Xvfb :0 is present and accepting connections"
        return False, "DISPLAY=:0 not available in container; Xvfb may not have started"
    except Exception as exc:
        return False, f"Linux framebuffer probe error: {exc}"


def _probe_android(ids: dict) -> tuple[bool, str]:
    serial = ids.get("adb_serial", "")
    if not serial:
        return False, "No adb_serial in provider_ids"
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "shell", "dumpsys", "SurfaceFlinger", "--latency", "SurfaceView"],
            capture_output=True, text=True, timeout=_TIMEOUT_S,
        )
        if result.returncode == 0:
            return True, "Android SurfaceFlinger framebuffer present"
        return False, "Android SurfaceFlinger probe failed — framebuffer may be unavailable"
    except Exception as exc:
        return False, f"Android framebuffer probe error: {exc}"


def _probe_qemu_vnc(ids: dict, family: str) -> tuple[bool, str]:
    vnc_display = ids.get("vnc_display")
    if vnc_display is None:
        return False, f"{family} VM has no vnc_display in provider_ids — framebuffer not configured"
    vnc_port = 5900 + int(vnc_display)
    # A VNC server listening on loopback means the guest display is up
    import socket
    try:
        with socket.create_connection(("127.0.0.1", vnc_port), timeout=3):
            return True, f"{family} VNC on port {vnc_port} is accepting connections"
    except OSError:
        return False, (
            f"{family} VNC port {vnc_port} not reachable — virtio-gpu/vga may not have initialised yet"
        )


def _probe_ios_sim(ids: dict) -> tuple[bool, str]:
    udid = ids.get("sim_udid", "")
    if not udid:
        return False, "No sim_udid in provider_ids"
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "io", udid, "screenshot", "/dev/null"],
            capture_output=True, timeout=_TIMEOUT_S,
        )
        if result.returncode == 0:
            return True, "iOS Simulator framebuffer capturable via simctl io"
        return False, f"simctl io screenshot failed (rc={result.returncode})"
    except Exception as exc:
        return False, f"iOS Simulator framebuffer probe error: {exc}"
