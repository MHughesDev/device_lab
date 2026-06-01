# adapters/windows/local_provision.py — QEMU-based Windows VM provisioner for local hosting
from __future__ import annotations
import asyncio
import os
import socket
import subprocess
import time
import uuid

from app.services.local.host_probe import probe_host

_VM_SSH_PORT_BASE = 15900
_SSH_WAIT_TIMEOUT_S = 300


async def provision(device: object, template: object) -> dict:
    """Provision a local Windows VM via QEMU.

    Requires KVM on Linux or WHPX on Windows. Hard-refused on Apple Silicon
    (no x86 Windows on arm64 without emulation).
    """
    caps = probe_host()
    if not caps.virtualization_available:
        raise RuntimeError(
            "Host virtualization (KVM or WHPX) is required for local Windows VMs. "
            "Enable KVM on Linux or Hyper-V on Windows."
        )
    if caps.os == "macos" and caps.arch == "arm64":
        raise RuntimeError(
            "x86 Windows cannot run on Apple Silicon. "
            "Use placement_policy=cloud_only or supply an arm64 Windows image."
        )

    device_id = str(getattr(device, "id", uuid.uuid4()))
    vm_name = f"devicelab-win-{device_id[:8]}"
    host_ssh_port = _allocate_port()
    image_path = _resolve_image(template)

    qemu_cmd = _build_qemu_cmd(image_path, host_ssh_port, vm_name)
    subprocess.Popen(qemu_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await _wait_for_ssh("127.0.0.1", host_ssh_port, timeout_s=_SSH_WAIT_TIMEOUT_S)

    return {
        "vm_name": vm_name,
        "vm_ip": "127.0.0.1",
        "ssh_port": host_ssh_port,
        "ssh_username": "Administrator",
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
        "Windows local template requires extra_config.image_path pointing to a .qcow2 disk image. "
        "See docs/operations/local-host-prerequisites.md for setup instructions."
    )


def _build_qemu_cmd(image_path: str, ssh_port: int, vm_name: str) -> list[str]:
    accel = "kvm" if os.path.exists("/dev/kvm") else "tcg"
    return [
        "qemu-system-x86_64",
        "-name", vm_name,
        "-m", "4096",
        "-smp", "2",
        "-accel", accel,
        "-drive", f"file={image_path},if=virtio,format=qcow2",
        "-net", "nic,model=virtio",
        "-net", f"user,hostfwd=tcp:127.0.0.1:{ssh_port}-:22",
        "-display", "none",
    ]


def _allocate_port() -> int:
    """Find a free port in the 15900+ range for SSH forwarding."""
    for port in range(_VM_SSH_PORT_BASE, _VM_SSH_PORT_BASE + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free ports in range 15900-15999 for VM SSH forwarding")


async def _wait_for_ssh(host: str, port: int, timeout_s: int = 300) -> None:
    """Poll TCP until the SSH port accepts connections."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except OSError:
            await asyncio.sleep(3)
    raise TimeoutError(f"SSH on {host}:{port} did not become available within {timeout_s}s")
