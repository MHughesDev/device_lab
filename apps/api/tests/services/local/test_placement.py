# test_placement.py — Placement policy resolution unit tests (Task 07-06)
from __future__ import annotations

import pytest

from app.services.local.host_probe import HostCapabilities
from app.services.local.placement import PlacementError, resolve_location


def _caps(os="linux", arch="x86_64", is_apple=False) -> HostCapabilities:
    return HostCapabilities(
        os=os,
        arch=arch,
        docker_available=True,
        virtualization_available=True,
        is_apple_hardware=is_apple,
        total_ram_mb=8192,
        total_vcpu=4,
        free_disk_mb=50_000,
    )


def test_cloud_only_ignores_host():
    caps = _caps(os="linux")
    loc = resolve_location("linux", "cloud_only", caps)
    assert loc == "cloud"


def test_prefer_local_falls_back_to_cloud_for_ios_sim_on_linux():
    caps = _caps(os="linux", is_apple=False)
    loc = resolve_location("ios_sim", "prefer_local", caps)
    assert loc == "cloud"


def test_local_only_unsupported_family_errors():
    caps = _caps(os="linux", is_apple=False)
    with pytest.raises(PlacementError):
        resolve_location("ios_sim", "local_only", caps)


def test_prefer_local_linux_on_linux_host():
    caps = _caps(os="linux")
    loc = resolve_location("linux", "prefer_local", caps)
    assert loc == "local"


def test_apple_host_can_run_macos_local():
    caps = _caps(os="macos", is_apple=True)
    loc = resolve_location("macos", "prefer_local", caps)
    assert loc == "local"


def test_non_apple_macos_host_falls_back():
    """macOS running on non-Apple hardware (e.g. Hackintosh/VM) must not offer macOS local."""
    caps = _caps(os="macos", is_apple=False)
    loc = resolve_location("macos", "prefer_local", caps)
    assert loc == "cloud"


def test_local_only_ios_sim_on_non_apple_errors():
    caps = _caps(os="macos", is_apple=False)
    with pytest.raises(PlacementError):
        resolve_location("ios_sim", "local_only", caps)


def test_apple_host_offers_ios_sim_local():
    caps = _caps(os="macos", is_apple=True)
    loc = resolve_location("ios_sim", "local_only", caps)
    assert loc == "local"
