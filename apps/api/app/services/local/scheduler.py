# scheduler.py — LocalScheduler: capacity model and admission control for local devices
from __future__ import annotations
import threading
from dataclasses import dataclass, field

from app.services.local.host_probe import HostCapabilities, probe_host


@dataclass
class ResourceEstimate:
    """Resource budget for one local device instance."""
    ram_mb: int = 0
    vcpu: int = 0
    disk_mb: int = 0


@dataclass
class AdmissionResult:
    allowed: bool
    reason: str = ""


class LocalScheduler:
    """Track committed local resources and enforce capacity limits.

    Thread-safe. One process-global instance (see module-level `_scheduler`).
    Admission control is reject-fast (no queue in v1).
    """

    def __init__(self, caps: HostCapabilities | None = None) -> None:
        self._caps = caps or probe_host()
        self._lock = threading.Lock()
        self._committed_ram_mb: int = 0
        self._committed_vcpu: int = 0
        self._committed_disk_mb: int = 0

    # ------------------------------------------------------------------
    # Capacity limits
    # ------------------------------------------------------------------

    # Reserve a safety margin so the host OS stays responsive
    _RAM_RESERVE_MB = 512
    _DISK_RESERVE_MB = 1024

    @property
    def _available_ram_mb(self) -> int:
        return max(0, self._caps.total_ram_mb - self._RAM_RESERVE_MB - self._committed_ram_mb)

    @property
    def _available_vcpu(self) -> int:
        return max(0, self._caps.total_vcpu - self._committed_vcpu)

    @property
    def _available_disk_mb(self) -> int:
        return max(0, self._caps.free_disk_mb - self._DISK_RESERVE_MB - self._committed_disk_mb)

    # ------------------------------------------------------------------
    # Admission interface
    # ------------------------------------------------------------------

    def admit(self, estimate: ResourceEstimate) -> AdmissionResult:
        """Atomically check and commit resources. Returns AdmissionResult.

        On success the resources are held until `release()` is called.
        """
        with self._lock:
            if estimate.ram_mb > self._available_ram_mb:
                return AdmissionResult(
                    allowed=False,
                    reason=(
                        f"insufficient_host_resources: need {estimate.ram_mb} MB RAM, "
                        f"available {self._available_ram_mb} MB"
                    ),
                )
            if estimate.vcpu > 0 and estimate.vcpu > self._available_vcpu:
                return AdmissionResult(
                    allowed=False,
                    reason=(
                        f"insufficient_host_resources: need {estimate.vcpu} vCPU, "
                        f"available {self._available_vcpu}"
                    ),
                )
            if estimate.disk_mb > self._available_disk_mb:
                return AdmissionResult(
                    allowed=False,
                    reason=(
                        f"insufficient_host_resources: need {estimate.disk_mb} MB disk, "
                        f"available {self._available_disk_mb} MB"
                    ),
                )
            self._committed_ram_mb += estimate.ram_mb
            self._committed_vcpu += estimate.vcpu
            self._committed_disk_mb += estimate.disk_mb
            return AdmissionResult(allowed=True)

    def release(self, estimate: ResourceEstimate) -> None:
        """Return previously admitted resources to the pool."""
        with self._lock:
            self._committed_ram_mb = max(0, self._committed_ram_mb - estimate.ram_mb)
            self._committed_vcpu = max(0, self._committed_vcpu - estimate.vcpu)
            self._committed_disk_mb = max(0, self._committed_disk_mb - estimate.disk_mb)

    # ------------------------------------------------------------------
    # Snapshot (for diagnostics / doctor command)
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "total_ram_mb": self._caps.total_ram_mb,
                "committed_ram_mb": self._committed_ram_mb,
                "available_ram_mb": self._available_ram_mb,
                "total_vcpu": self._caps.total_vcpu,
                "committed_vcpu": self._committed_vcpu,
                "available_vcpu": self._available_vcpu,
                "free_disk_mb": self._caps.free_disk_mb,
                "committed_disk_mb": self._committed_disk_mb,
                "available_disk_mb": self._available_disk_mb,
            }


# Process-global scheduler instance (lazy-initialized on first use)
_scheduler: LocalScheduler | None = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> LocalScheduler:
    global _scheduler
    if _scheduler is None:
        with _scheduler_lock:
            if _scheduler is None:
                _scheduler = LocalScheduler()
    return _scheduler
