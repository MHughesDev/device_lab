# ledger.py — Host Resource Ledger: durable committed-vs-total RAM/vCPU/disk accounting (Phase 08)
from __future__ import annotations
import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.services.local.host_probe import HostCapabilities, probe_host

log = logging.getLogger(__name__)

# Fraction of total RAM reserved for the host OS — never committed to devices.
_HOST_RAM_HEADROOM_FRACTION = 0.20


@dataclass(frozen=True)
class ResourceClaim:
    ram_mb: int
    vcpu: float
    disk_mb: int


class ResourceLedger:
    """Durable committed-vs-total resource accounting for local devices.

    Thread-safe. Persists reservations to DB so the ledger survives control-plane
    restarts (reconcile_ledger() rebuilds from DB on boot, see ledger_reconcile.py).

    A device holds its full reservation from ``provisioning`` until ``terminated``.
    There is no intermediate suspended state — resources are either reserved or free.
    """

    def __init__(self, caps: HostCapabilities | None = None) -> None:
        self._caps = caps or probe_host()
        self._lock = threading.Lock()
        # headroom: 20% of total RAM is off-limits for devices
        self._headroom_mb = int(self._caps.total_ram_mb * _HOST_RAM_HEADROOM_FRACTION)

    # ------------------------------------------------------------------
    # Phase 12 settings wiring
    # ------------------------------------------------------------------

    def apply_settings(self, db, workspace_id) -> None:
        """Re-read Phase 12 host budget settings and update ledger totals.

        Refuses to lower the effective device RAM budget below currently
        committed resources (raises ValueError). Caller must confirm/force.
        """
        from app.services.settings_service import get_group
        host_cfg = get_group(db, workspace_id, "host")

        with self._lock:
            new_headroom_pct: int = int(host_cfg.get("headroom_pct") or 20)
            new_headroom_mb = int(self._caps.total_ram_mb * new_headroom_pct / 100)

            budget_ram = host_cfg.get("device_ram_budget_mb")
            if budget_ram is not None:
                committed_ram = self.committed().ram_mb
                if int(budget_ram) < committed_ram:
                    raise ValueError(
                        f"Cannot lower RAM budget to {budget_ram} MB — "
                        f"{committed_ram} MB already committed to live devices"
                    )
                from app.services.local.host_probe import HostCapabilities as HC
                self._caps = HC(
                    total_ram_mb=int(budget_ram) + new_headroom_mb,
                    total_vcpu=float(host_cfg.get("device_cpu_budget_cores") or self._caps.total_vcpu),
                    free_disk_mb=self._caps.free_disk_mb,
                )

            self._headroom_mb = new_headroom_mb
            log.info(
                "Ledger settings applied: headroom=%d MB, total_ram=%d MB",
                self._headroom_mb, self._caps.total_ram_mb,
            )

    # ------------------------------------------------------------------
    # Capacity queries
    # ------------------------------------------------------------------

    def totals(self) -> ResourceClaim:
        """Usable totals after subtracting host headroom."""
        return ResourceClaim(
            ram_mb=max(0, self._caps.total_ram_mb - self._headroom_mb),
            vcpu=float(self._caps.total_vcpu),
            disk_mb=self._caps.free_disk_mb,
        )

    def committed(self) -> ResourceClaim:
        """Sum of live HostReservation rows from the DB."""
        from app.core.db import engine
        from sqlmodel import Session, select, func
        from app.models import HostReservation

        with Session(engine) as db:
            rows = db.exec(select(HostReservation)).all()
            return ResourceClaim(
                ram_mb=sum(r.ram_mb for r in rows),
                vcpu=sum(r.vcpu for r in rows),
                disk_mb=sum(r.disk_mb for r in rows),
            )

    def can_admit(self, claim: ResourceClaim) -> bool:
        totals = self.totals()
        committed = self.committed()
        if claim.ram_mb > (totals.ram_mb - committed.ram_mb):
            return False
        if claim.vcpu > (totals.vcpu - committed.vcpu):
            return False
        if claim.disk_mb > (totals.disk_mb - committed.disk_mb):
            return False
        return True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reserve(self, device_id: str | uuid.UUID, claim: ResourceClaim) -> None:
        """Persist a reservation for this device. Idempotent — update if already exists."""
        from app.core.db import engine
        from sqlmodel import Session, select
        from app.models import HostReservation

        did = uuid.UUID(str(device_id)) if not isinstance(device_id, uuid.UUID) else device_id
        with self._lock:
            with Session(engine) as db:
                existing = db.exec(
                    select(HostReservation).where(HostReservation.device_id == did)
                ).first()
                if existing:
                    existing.ram_mb = claim.ram_mb
                    existing.vcpu = claim.vcpu
                    existing.disk_mb = claim.disk_mb
                    db.add(existing)
                else:
                    db.add(HostReservation(
                        device_id=did,
                        ram_mb=claim.ram_mb,
                        vcpu=claim.vcpu,
                        disk_mb=claim.disk_mb,
                        created_at=datetime.now(UTC),
                    ))
                db.commit()
        log.debug("Ledger reserved %s MB RAM for device %s", claim.ram_mb, did)

    def release(self, device_id: str | uuid.UUID) -> None:
        """Delete the reservation for this device. Idempotent — missing rows are ignored."""
        from app.core.db import engine
        from sqlmodel import Session, select
        from app.models import HostReservation

        did = uuid.UUID(str(device_id)) if not isinstance(device_id, uuid.UUID) else device_id
        with self._lock:
            with Session(engine) as db:
                row = db.exec(
                    select(HostReservation).where(HostReservation.device_id == did)
                ).first()
                if row:
                    db.delete(row)
                    db.commit()
                    log.debug("Ledger released reservation for device %s", did)

    # ------------------------------------------------------------------
    # Settings integration (Phase 12)
    # ------------------------------------------------------------------

    def apply_settings(self, db, workspace_id) -> None:
        """Read the 'host' settings group and update headroom / caps in-place.

        Only non-None values are applied.  Guards:
        - Never sets headroom above what leaves the currently committed RAM
          still admissible (i.e. headroom_mb < total_ram_mb - committed_ram_mb).
        - Never sets total usable RAM below what is already committed.
        """
        try:
            from app.services.settings_service import get_group
            host_cfg = get_group(db, workspace_id, "host")
        except Exception as exc:
            log.warning("apply_settings: could not load host settings: %s", exc)
            return

        with self._lock:
            # --- headroom_pct ---
            headroom_pct = host_cfg.get("headroom_pct")
            if headroom_pct is not None:
                new_headroom_mb = int(self._caps.total_ram_mb * headroom_pct / 100)
                # Safety: never push headroom so high that committed RAM would be
                # over the usable budget.
                committed_ram = self.committed().ram_mb
                max_safe_headroom = max(0, self._caps.total_ram_mb - committed_ram)
                new_headroom_mb = min(new_headroom_mb, max_safe_headroom)
                self._headroom_mb = new_headroom_mb
                log.debug(
                    "apply_settings: headroom set to %d MB (%d%% of %d MB total)",
                    new_headroom_mb, headroom_pct, self._caps.total_ram_mb,
                )

            # --- device_ram_budget_mb ---
            ram_budget = host_cfg.get("device_ram_budget_mb")
            if ram_budget is not None:
                # Override total_ram_mb on the caps object by swapping the dataclass
                from app.services.local.host_probe import HostCapabilities
                self._caps = HostCapabilities(
                    os=self._caps.os,
                    arch=self._caps.arch,
                    docker_available=self._caps.docker_available,
                    virtualization_available=self._caps.virtualization_available,
                    is_apple_hardware=self._caps.is_apple_hardware,
                    total_ram_mb=int(ram_budget),
                    total_vcpu=self._caps.total_vcpu,
                    free_disk_mb=self._caps.free_disk_mb,
                )
                log.debug("apply_settings: RAM budget overridden to %d MB", ram_budget)

            # --- device_cpu_budget_cores ---
            cpu_budget = host_cfg.get("device_cpu_budget_cores")
            if cpu_budget is not None:
                from app.services.local.host_probe import HostCapabilities
                self._caps = HostCapabilities(
                    os=self._caps.os,
                    arch=self._caps.arch,
                    docker_available=self._caps.docker_available,
                    virtualization_available=self._caps.virtualization_available,
                    is_apple_hardware=self._caps.is_apple_hardware,
                    total_ram_mb=self._caps.total_ram_mb,
                    total_vcpu=int(cpu_budget),
                    free_disk_mb=self._caps.free_disk_mb,
                )
                log.debug("apply_settings: CPU budget overridden to %d vCPUs", cpu_budget)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        totals = self.totals()
        committed = self.committed()
        return {
            "total_ram_mb": totals.ram_mb,
            "committed_ram_mb": committed.ram_mb,
            "available_ram_mb": totals.ram_mb - committed.ram_mb,
            "headroom_mb": self._headroom_mb,
            "total_vcpu": totals.vcpu,
            "committed_vcpu": committed.vcpu,
            "available_vcpu": totals.vcpu - committed.vcpu,
            "total_disk_mb": totals.disk_mb,
            "committed_disk_mb": committed.disk_mb,
            "available_disk_mb": totals.disk_mb - committed.disk_mb,
        }


# Process-global ledger instance (lazy-initialized on first use)
_ledger: ResourceLedger | None = None
_ledger_lock = threading.Lock()


def get_ledger() -> ResourceLedger:
    global _ledger
    if _ledger is None:
        with _ledger_lock:
            if _ledger is None:
                _ledger = ResourceLedger()
    return _ledger
