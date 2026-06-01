# local_provision.py — Linux local provisioner: Docker container lifecycle + Xvfb framebuffer
from __future__ import annotations
import json
import logging
import uuid

from app.services.local.reaper import LABEL_DEVICE, LABEL_WORKSPACE

log = logging.getLogger(__name__)

# Default image used when no template-level image is specified
_DEFAULT_IMAGE = "ubuntu:24.04"

# Container resource defaults for a local Linux device
_DEFAULT_MEM_LIMIT = "512m"
_DEFAULT_CPU_QUOTA = 50_000  # 0.5 vCPU (in units of 1/100000 of a CPU period)

# Xvfb resolution — configurable via template extra_config.resolution
_DEFAULT_RESOLUTION = "1920x1080x24"

# Command injected as the container entrypoint to start Xvfb before anything else.
# Sets DISPLAY=:0 for the container session so screenshot/AX-tree tools resolve it.
# Falls back gracefully if Xvfb is not installed (headless-only observation still works).
_XVFB_ENTRYPOINT = (
    "sh -c 'which Xvfb >/dev/null 2>&1 && Xvfb :0 -screen 0 {resolution} -nolisten tcp &sleep 1; "
    "export DISPLAY=:0; tail -f /dev/null'"
)


def _get_docker():
    import docker
    return docker.from_env()


async def provision(device: object, template: object) -> dict:
    """Create and start a labelled Docker container for a local Linux device.

    Starts Xvfb :0 as the first process so DISPLAY=:0 resolves for all
    screenshot/recording/AX-tree tools. Returns a provider_ids dict with
    `container_id` so ChannelFactory can resolve DockerExecChannel.
    """
    workspace_id = str(getattr(device, "workspace_id", ""))
    device_id = str(getattr(device, "id", ""))

    cap_json = getattr(template, "capability_json", None)
    image = _DEFAULT_IMAGE
    resolution = _DEFAULT_RESOLUTION
    if cap_json:
        try:
            cap = json.loads(cap_json)
            image = cap.get("local_image", image)
            resolution = cap.get("resolution", resolution)
        except Exception:
            pass

    entrypoint_cmd = _XVFB_ENTRYPOINT.format(resolution=resolution)

    client = _get_docker()
    container = client.containers.run(
        image=image,
        detach=True,
        remove=False,
        stdin_open=True,
        tty=True,
        mem_limit=_DEFAULT_MEM_LIMIT,
        cpu_quota=_DEFAULT_CPU_QUOTA,
        environment={"DISPLAY": ":0"},
        labels={
            LABEL_WORKSPACE: workspace_id,
            LABEL_DEVICE: device_id,
        },
        name=f"devicelab-{device_id[:8]}",
        command=entrypoint_cmd,
    )
    log.debug("Linux container %s started with Xvfb on :0", container.id[:12])
    _emit_provisioner(device_id, f"Container {container.id[:12]} started (image={image}, display=:0)")
    return {"container_id": container.id, "location": "local", "display": ":0"}


def _emit_provisioner(device_id: str, message: str, level: str = "info") -> None:
    """Fire-and-forget log bus emission for provisioner events."""
    try:
        from app.services.device_log_bus import get_log_bus
        get_log_bus().emit(device_id, level=level, source="provisioner", message=message)
    except Exception:
        pass


async def terminate(device: object) -> None:
    """Stop and remove the container. Idempotent — missing containers are ignored."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    container_id = ids.get("container_id")
    if not container_id:
        return

    client = _get_docker()
    try:
        container = client.containers.get(container_id)
        try:
            container.stop(timeout=10)
        except Exception:
            pass
        container.remove(force=True)
    except Exception:
        # Container already gone — idempotent
        pass
