# test_ledger.py — Tests for Host Resource Ledger (Phase 08, tasks 08-07, 08-08, 08-09)
from __future__ import annotations
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.local.ledger import ResourceClaim, ResourceLedger
from app.services.local.host_probe import HostCapabilities


def _caps(ram_mb: int = 8192, vcpu: int = 4, disk_mb: int = 50000) -> HostCapabilities:
    return HostCapabilities(
        total_ram_mb=ram_mb,
        total_vcpu=vcpu,
        free_disk_mb=disk_mb,
        virtualization_available=True,
        os="linux",
        arch="x86_64",
        is_apple_hardware=False,
        docker_available=True,
    )


def _make_ledger(ram_mb: int = 8192, vcpu: int = 4, disk_mb: int = 50000) -> ResourceLedger:
    return ResourceLedger(caps=_caps(ram_mb, vcpu, disk_mb))


class TestResourceLedgerTotals:
    def test_headroom_is_never_committed(self) -> None:
        ledger = _make_ledger(ram_mb=10000)
        totals = ledger.totals()
        # 20% headroom → usable RAM is at most 80% of total
        assert totals.ram_mb <= 8000

    def test_totals_respect_headroom_fraction(self) -> None:
        ledger = _make_ledger(ram_mb=10000)
        assert ledger.totals().ram_mb == 8000  # 10000 * 0.8


class TestResourceLedgerCanAdmit:
    def test_can_admit_rejects_over_ram(self) -> None:
        ledger = _make_ledger(ram_mb=1000)
        huge_claim = ResourceClaim(ram_mb=5000, vcpu=0.5, disk_mb=100)
        # After 20% headroom: only 800 MB usable; 5000 > 800 → reject
        with patch.object(ledger, "committed", return_value=ResourceClaim(0, 0.0, 0)):
            assert not ledger.can_admit(huge_claim)

    def test_can_admit_accepts_within_budget(self) -> None:
        ledger = _make_ledger(ram_mb=8192, vcpu=4, disk_mb=50000)
        small_claim = ResourceClaim(ram_mb=256, vcpu=0.5, disk_mb=1024)
        with patch.object(ledger, "committed", return_value=ResourceClaim(0, 0.0, 0)):
            assert ledger.can_admit(small_claim)

    def test_can_admit_rejects_over_vcpu(self) -> None:
        ledger = _make_ledger(ram_mb=8192, vcpu=2, disk_mb=50000)
        claim = ResourceClaim(ram_mb=512, vcpu=4.0, disk_mb=1024)
        with patch.object(ledger, "committed", return_value=ResourceClaim(0, 0.0, 0)):
            assert not ledger.can_admit(claim)


class TestResourceLedgerReserveRelease:
    def test_release_on_terminate_frees_all_resources(self) -> None:
        ledger = _make_ledger()
        device_id = uuid.uuid4()
        claim = ResourceClaim(ram_mb=512, vcpu=1.0, disk_mb=4096)

        released_ids: list = []

        def fake_reserve(did, c):
            pass

        def fake_release(did):
            released_ids.append(str(did))

        def fake_committed():
            return ResourceClaim(0, 0.0, 0)

        with (
            patch.object(ledger, "reserve", side_effect=fake_reserve),
            patch.object(ledger, "release", side_effect=fake_release),
            patch.object(ledger, "committed", side_effect=fake_committed),
        ):
            ledger.reserve(device_id, claim)
            ledger.release(device_id)
            assert str(device_id) in released_ids

    def test_snapshot_reports_committed_and_available(self) -> None:
        ledger = _make_ledger(ram_mb=8192, vcpu=4, disk_mb=50000)
        committed = ResourceClaim(ram_mb=512, vcpu=1.0, disk_mb=4096)

        with patch.object(ledger, "committed", return_value=committed):
            snap = ledger.snapshot()
            assert snap["committed_ram_mb"] == 512
            assert snap["available_ram_mb"] == ledger.totals().ram_mb - 512
            assert "headroom_mb" in snap
