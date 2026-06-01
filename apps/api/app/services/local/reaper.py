# reaper.py — Reaper: GC orphaned local resources that lack a live Device row
from __future__ import annotations
import logging
import uuid

log = logging.getLogger(__name__)

# DeviceLab labels applied to every locally-created container / VM
LABEL_WORKSPACE = "devicelab.workspace"
LABEL_DEVICE = "devicelab.device"


def reap_orphans(db_device_ids: set[str]) -> dict:
    """Remove locally-created resources that have no matching Device row.

    `db_device_ids` — set of device UUID strings that are currently live
    (state not in terminal states) in the database.

    Returns a summary dict: {"removed_containers": [...], "skipped": [...]}
    """
    removed: list[str] = []
    skipped: list[str] = []

    removed_containers = _reap_docker(db_device_ids, removed, skipped)

    return {
        "removed_containers": removed_containers,
        "skipped": skipped,
    }


def _reap_docker(db_device_ids: set[str], removed: list[str], skipped: list[str]) -> list[str]:
    """Reap Docker containers labelled with DeviceLab labels but missing a live device row."""
    removed_containers: list[str] = []
    try:
        import docker
    except ImportError:
        return removed_containers

    try:
        client = docker.from_env()
    except Exception as exc:
        log.debug("Docker not available for reaper: %s", exc)
        return removed_containers

    try:
        containers = client.containers.list(
            all=True,
            filters={"label": LABEL_DEVICE},
        )
    except Exception as exc:
        log.warning("Reaper: failed to list Docker containers: %s", exc)
        return removed_containers

    for container in containers:
        labels = container.labels or {}
        device_id = labels.get(LABEL_DEVICE, "")

        if not device_id:
            skipped.append(container.id)
            continue

        if device_id in db_device_ids:
            # Live device — leave it alone
            continue

        try:
            log.info("Reaper: removing orphan container %s (device_id=%s)", container.id, device_id)
            container.stop(timeout=5)
            container.remove(force=True)
            removed_containers.append(container.id)
        except Exception as exc:
            log.warning("Reaper: failed to remove container %s: %s", container.id, exc)
            skipped.append(container.id)

    return removed_containers


async def reap_from_db(db) -> dict:
    """Convenience wrapper: pull live device IDs from DB and reap orphans.

    `db` — SQLModel Session.
    """
    from sqlmodel import select
    from app.models import Device

    terminal = {"terminated", "failed"}
    stmt = select(Device.id).where(~Device.state.in_(terminal))  # type: ignore[attr-defined]
    live_ids = {str(row) for row in db.exec(stmt).all()}
    return reap_orphans(live_ids)
