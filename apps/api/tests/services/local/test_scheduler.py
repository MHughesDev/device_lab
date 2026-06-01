# test_scheduler.py — LocalScheduler unit tests (Task 07-04)
from __future__ import annotations

import pytest

from app.services.local.host_probe import HostCapabilities
from app.services.local.scheduler import LocalScheduler, ResourceEstimate


def _make_scheduler(ram_mb: int = 8192, vcpu: int = 4, free_disk_mb: int = 50_000) -> LocalScheduler:
    caps = HostCapabilities(
        os="linux",
        arch="x86_64",
        docker_available=True,
        virtualization_available=True,
        is_apple_hardware=False,
        total_ram_mb=ram_mb,
        total_vcpu=vcpu,
        free_disk_mb=free_disk_mb,
    )
    return LocalScheduler(caps)


def test_admit_allows_within_capacity():
    sched = _make_scheduler(ram_mb=4096)
    result = sched.admit(ResourceEstimate(ram_mb=512, vcpu=1, disk_mb=1024))
    assert result.allowed is True


def test_admit_rejects_when_over_ram():
    sched = _make_scheduler(ram_mb=1024)  # 1 GB total
    # 1024 - 512 reserve = 512 MB available; requesting 1024 should fail
    result = sched.admit(ResourceEstimate(ram_mb=1024, vcpu=0, disk_mb=0))
    assert result.allowed is False
    assert "insufficient_host_resources" in result.reason
    assert "RAM" in result.reason


def test_admit_rejects_when_over_disk():
    sched = _make_scheduler(free_disk_mb=2048)  # 2 GB free
    # 2048 - 1024 reserve = 1024 MB available; requesting 2048 should fail
    result = sched.admit(ResourceEstimate(ram_mb=0, vcpu=0, disk_mb=2048))
    assert result.allowed is False
    assert "disk" in result.reason


def test_admit_accounts_for_committed():
    sched = _make_scheduler(ram_mb=4096)
    # Admit two devices — second takes us over
    r1 = sched.admit(ResourceEstimate(ram_mb=1500, vcpu=1, disk_mb=0))
    assert r1.allowed is True
    r2 = sched.admit(ResourceEstimate(ram_mb=1500, vcpu=1, disk_mb=0))
    assert r2.allowed is True
    # Third should fail: 4096 - 512 reserve - 3000 committed = 584 available, request 1000
    r3 = sched.admit(ResourceEstimate(ram_mb=1000, vcpu=0, disk_mb=0))
    assert r3.allowed is False


def test_release_restores_capacity():
    sched = _make_scheduler(ram_mb=2048)
    est = ResourceEstimate(ram_mb=1000, vcpu=1, disk_mb=0)
    r1 = sched.admit(est)
    assert r1.allowed is True
    # Release and admit again — should succeed
    sched.release(est)
    r2 = sched.admit(est)
    assert r2.allowed is True


def test_fsm_blocks_on_scheduler_rejection(tmp_path):
    """FSM preflight_pass transitions to preflight_blocked when scheduler rejects."""
    from unittest.mock import MagicMock, patch
    from sqlmodel import Session

    from app.services.device_fsm import DeviceFSM
    from app.models import Device
    import uuid
    from datetime import UTC, datetime

    # Build a minimal device with location=local
    device = MagicMock(spec=Device)
    device.state = "requested"
    device.location = "local"
    device.workspace_id = uuid.uuid4()

    db = MagicMock(spec=Session)
    fsm = DeviceFSM(device, db)

    # Make the scheduler always reject
    tight_sched = _make_scheduler(ram_mb=512)  # only 512 MB, reserve eats it all
    with patch("app.services.local.scheduler.get_scheduler", return_value=tight_sched):
        from app.services.device_fsm import _LocalAdmissionBlocked
        with pytest.raises(_LocalAdmissionBlocked):
            fsm.transition("preflight_pass")

    assert device.state == "preflight_blocked" or fsm.current_state == "preflight_blocked"
