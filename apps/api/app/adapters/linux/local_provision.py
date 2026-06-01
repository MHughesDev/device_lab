# local_provision.py — Linux local provisioner: Docker container lifecycle
from __future__ import annotations
import json
import uuid

from app.services.local.reaper import LABEL_DEVICE, LABEL_WORKSPACE

# Default image used when no template-level image is specified
_DEFAULT_IMAGE = "ubuntu:24.04"

# Container resource defaults for a local Linux device
_DEFAULT_MEM_LIMIT = "512m"
_DEFAULT_CPU_QUOTA = 50_000  # 0.5 vCPU (in units of 1/100000 of a CPU period)


def _get_docker():
    import docker
    return docker.from_env()


async def provision(device: object, template: object) -> dict:
    """Create and start a labelled Docker container for a local Linux device.

    Returns a provider_ids dict with `container_id` so ChannelFactory
    can resolve DockerExecChannel on subsequent calls.
    """
    workspace_id = str(getattr(device, "workspace_id", ""))
    device_id = str(getattr(device, "id", ""))

    cap_json = getattr(template, "capability_json", None)
    image = _DEFAULT_IMAGE
    if cap_json:
        try:
            cap = json.loads(cap_json)
            image = cap.get("local_image", image)
        except Exception:
            pass

    client = _get_docker()
    container = client.containers.run(
        image=image,
        detach=True,
        remove=False,
        stdin_open=True,
        tty=True,
        mem_limit=_DEFAULT_MEM_LIMIT,
        cpu_quota=_DEFAULT_CPU_QUOTA,
        labels={
            LABEL_WORKSPACE: workspace_id,
            LABEL_DEVICE: device_id,
        },
        name=f"devicelab-{device_id[:8]}",
    )
    return {"container_id": container.id, "location": "local"}


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
