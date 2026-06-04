"""Host resource ledger route — Phase 11 (11-14)."""

import multiprocessing
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/host", tags=["host"])


class HostResources(BaseModel):
    total_ram_mb: int
    committed_ram_mb: int
    available_ram_mb: int
    total_cpu_cores: int
    committed_cpu_cores: int
    device_count: int
    max_devices: int


@router.get("/resources", response_model=HostResources)
def get_host_resources() -> HostResources:
    """Return current host resource usage from the Phase 08 ResourceLedger."""
    try:
        from app.services.resource_ledger import ResourceLedger
        ledger = ResourceLedger.get()
        return HostResources(
            total_ram_mb=ledger.total_ram_mb,
            committed_ram_mb=ledger.committed_ram_mb,
            available_ram_mb=max(0, ledger.total_ram_mb - ledger.committed_ram_mb),
            total_cpu_cores=ledger.total_cpu_cores,
            committed_cpu_cores=ledger.committed_cpu_cores,
            device_count=ledger.device_count,
            max_devices=ledger.max_devices,
        )
    except Exception:
        # Graceful fallback using OS values when ledger is unavailable
        import os
        cpu = multiprocessing.cpu_count()
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total_kb = int(line.split()[1])
                        break
                else:
                    total_kb = 8 * 1024 * 1024
        except OSError:
            total_kb = 8 * 1024 * 1024
        total_mb = total_kb // 1024
        return HostResources(
            total_ram_mb=total_mb,
            committed_ram_mb=0,
            available_ram_mb=total_mb,
            total_cpu_cores=cpu,
            committed_cpu_cores=0,
            device_count=0,
            max_devices=10,
        )
