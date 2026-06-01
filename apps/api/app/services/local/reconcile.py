# services/local/reconcile.py — Reconcile DB Device rows against local resource state + ledger
from __future__ import annotations
import json
import logging

log = logging.getLogger(__name__)

_TERMINAL_STATES = frozenset({"terminated", "failed", "stopped"})


async def reconcile_local_devices(db) -> dict:
    """Called on control-plane startup to reconcile local device state.

    For each non-terminal local Device row: probe the actual resource.
    - Alive  → re-adopted (left untouched).
    - Gone   → state=failed, phase=lost_on_restart.
    - Error  → recorded in result["errors"], device left as-is.

    Never deletes resources — only updates DB state.
    """
    from sqlmodel import select
    from app.models import Device

    results: dict = {"re_adopted": [], "marked_lost": [], "errors": []}

    stmt = select(Device).where(
        Device.location == "local",
        Device.state.not_in(list(_TERMINAL_STATES)),
    )
    local_devices = db.exec(stmt).all()

    for device in local_devices:
        device_id = str(device.id)
        try:
            alive = await _probe_alive(device)
            if alive:
                results["re_adopted"].append(device_id)
            else:
                device.state = "failed"
                device.phase = "lost_on_restart"
                db.add(device)
                results["marked_lost"].append(device_id)
                log.warning("Local device %s not found on restart; marked failed", device_id)
        except Exception as exc:
            results["errors"].append({"device_id": device_id, "error": str(exc)})
            log.exception("Error reconciling device %s", device_id)

    db.commit()

    # Rebuild ledger from live device state after device reconciliation
    await reconcile_ledger(db)

    return results


async def reconcile_ledger(db) -> dict:
    """Rebuild the Host Resource Ledger from current live Device rows.

    Called on startup after device reconciliation. Drops reservations for
    terminated/failed devices; ensures live devices have reservations.
    Prevents leaked reservations after a crash.
    """
    from sqlmodel import select
    from app.models import Device, HostReservation

    result: dict = {"reserved": [], "released": [], "errors": []}

    try:
        from app.services.local.ledger import get_ledger
        from app.services.device_fsm import _device_resource_claim
    except ImportError:
        log.warning("Ledger not available; skipping ledger reconciliation")
        return result

    ledger = get_ledger()

    # Live (non-terminal) local devices should have reservations
    live_stmt = select(Device).where(
        Device.location == "local",
        Device.state.not_in(list(_TERMINAL_STATES)),
    )
    live_devices = db.exec(live_stmt).all()
    live_ids = {str(d.id) for d in live_devices}

    for device in live_devices:
        device_id = str(device.id)
        try:
            claim = _device_resource_claim(device)
            ledger.reserve(device.id, claim)
            result["reserved"].append(device_id)
        except Exception as exc:
            result["errors"].append({"device_id": device_id, "error": str(exc)})
            log.exception("Error reserving ledger for device %s", device_id)

    # Drop reservations for devices that no longer exist or are terminal
    reservation_stmt = select(HostReservation)
    all_reservations = db.exec(reservation_stmt).all()
    for reservation in all_reservations:
        rid = str(reservation.device_id)
        if rid not in live_ids:
            try:
                ledger.release(reservation.device_id)
                result["released"].append(rid)
                log.info("Ledger: released leaked reservation for device %s", rid)
            except Exception as exc:
                result["errors"].append({"device_id": rid, "error": str(exc)})

    log.info(
        "Ledger reconciled: %d reserved, %d released, %d errors",
        len(result["reserved"]), len(result["released"]), len(result["errors"]),
    )
    return result


async def _probe_alive(device: object) -> bool:
    """Return True if the local resource backing this device still exists."""
    family: str = getattr(device, "family", "")
    ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")

    if family == "linux":
        return _docker_container_alive(ids.get("container_id", ""))
    if family == "android":
        return _adb_device_alive(ids.get("adb_serial", ""))
    if family in ("windows", "macos"):
        return _tcp_port_open(ids.get("vm_ip", "127.0.0.1"), int(ids.get("ssh_port", 22)))
    if family == "ios_sim":
        return _simctl_booted(ids.get("sim_udid", ""))
    return False


def _docker_container_alive(container_id: str) -> bool:
    if not container_id:
        return False
    try:
        import docker
        client = docker.from_env()
        container = client.containers.get(container_id)
        return container.status == "running"
    except Exception:
        return False


def _adb_device_alive(serial: str) -> bool:
    if not serial:
        return False
    try:
        import subprocess
        result = subprocess.run(
            ["adb", "-s", serial, "get-state"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0 and "device" in result.stdout
    except Exception:
        return False


def _tcp_port_open(host: str, port: int) -> bool:
    try:
        import socket
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError:
        return False


def _simctl_booted(udid: str) -> bool:
    if not udid:
        return False
    try:
        import subprocess
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", udid],
            capture_output=True, text=True, timeout=10,
        )
        return "Booted" in result.stdout
    except Exception:
        return False
