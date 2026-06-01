# adapters/macos/local_provision.py — QEMU/HVF macOS VM provisioner (Apple hardware only)
from __future__ import annotations
import asyncio
import os
import socket
import subprocess
import time
import uuid

from app.services.local.host_probe import probe_host
from app.services.local.placement import PlacementError

_VM_SSH_PORT_BASE = 16000
_SSH_WAIT_TIMEOUT_S = 300


async def provision(device: object, template: object) -> dict:
    """Provision a local macOS VM via QEMU + HVF.

    Hard-refused on non-Apple hardware; PlacementError surfaces as 4xx to the caller.
    """
    caps = probe_host()
    if not caps.is_apple_hardware:
        raise PlacementError(
            "macOS local devices require Apple hardware. "
            "Set placement_policy=cloud_only on non-Apple hosts."
        )

    device_id = str(getattr(device, "id", uuid.uuid4()))
    vm_name = f"devicelab-macos-{device_id[:8]}"
    host_ssh_port = _allocate_port()
    image_path = _resolve_image(template)

    qemu_cmd = _build_qemu_cmd(image_path, host_ssh_port, vm_name)
    subprocess.Popen(qemu_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await _wait_for_ssh("127.0.0.1", host_ssh_port, timeout_s=_SSH_WAIT_TIMEOUT_S)

    return {
        "vm_name": vm_name,
        "vm_ip": "127.0.0.1",
        "ssh_port": host_ssh_port,
        "ssh_username": "user",
        "location": "local",
    }


async def terminate(device: object) -> None:
    """Kill the QEMU process for this VM. Idempotent."""
    import json
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    vm_name = ids.get("vm_name")
    if not vm_name:
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: subprocess.run(["pkill", "-f", f"qemu.*{vm_name}"], capture_output=True),
    )


def _resolve_image(template: object) -> str:
    extra = getattr(template, "extra_config", None) or {}
    path = extra.get("image_path", "") if isinstance(extra, dict) else ""
    if path and os.path.exists(path):
        return path
    raise FileNotFoundError(
        "macOS local template requires extra_config.image_path pointing to a macOS .qcow2 image. "
        "See docs/operations/local-host-prerequisites.md."
    )


def _build_qemu_cmd(image_path: str, ssh_port: int, vm_name: str) -> list[str]:
    return [
        "qemu-system-aarch64",
        "-name", vm_name,
        "-m", "8192",
        "-smp", "4",
        "-accel", "hvf",  # macOS Hypervisor.framework
        "-cpu", "host",
        "-drive", f"file={image_path},if=virtio,format=qcow2",
        "-net", "nic,model=virtio-net-pci",
        "-net", f"user,hostfwd=tcp:127.0.0.1:{ssh_port}-:22",
        "-display", "none",
    ]


def _allocate_port() -> int:
    for port in range(_VM_SSH_PORT_BASE, _VM_SSH_PORT_BASE + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free ports in range 16000-16099 for VM SSH forwarding")


async def _wait_for_ssh(host: str, port: int, timeout_s: int = 300) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except OSError:
            await asyncio.sleep(3)
    raise TimeoutError(f"SSH on {host}:{port} did not become available within {timeout_s}s")
