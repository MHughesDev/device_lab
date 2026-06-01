# test_host_probe.py — HostCapabilities probe unit tests (Task 07-03)
from __future__ import annotations
from unittest.mock import MagicMock, patch

import pytest

from app.services.local.host_probe import HostCapabilities, probe_host


def _fake_psutil(total_ram: int = 8 * 1024**3, vcpu: int = 4, free_disk: int = 50 * 1024**3):
    psutil = MagicMock()
    vm = MagicMock()
    vm.total = total_ram
    psutil.virtual_memory.return_value = vm
    psutil.cpu_count.return_value = vcpu
    du = MagicMock()
    du.free = free_disk
    psutil.disk_usage.return_value = du
    return psutil


def test_probe_detects_os_and_arch():
    with (
        patch("platform.system", return_value="Linux"),
        patch("platform.machine", return_value="x86_64"),
        patch("shutil.which", return_value=None),  # no docker
        patch("os.path.exists", return_value=False),  # no /dev/kvm
        patch("app.services.local.host_probe._detect_apple_hardware", return_value=False),
        patch("builtins.__import__", side_effect=lambda name, *a, **k: __import__(name, *a, **k)),
    ):
        # Patch psutil at import time
        import sys
        fake_psutil = _fake_psutil()
        with patch.dict("sys.modules", {"psutil": fake_psutil}):
            caps = probe_host()

    assert caps.os == "linux"
    assert caps.arch == "x86_64"
    assert caps.is_apple_hardware is False


def test_probe_reports_apple_hardware_false_on_linux():
    with (
        patch("platform.system", return_value="Linux"),
        patch("platform.machine", return_value="x86_64"),
        patch("shutil.which", return_value=None),
        patch("os.path.exists", return_value=False),
    ):
        import sys
        fake_psutil = _fake_psutil()
        with patch.dict("sys.modules", {"psutil": fake_psutil}):
            caps = probe_host()

    assert caps.is_apple_hardware is False


def test_probe_returns_host_capabilities_dataclass():
    with (
        patch("platform.system", return_value="Linux"),
        patch("platform.machine", return_value="aarch64"),
        patch("shutil.which", return_value=None),
        patch("os.path.exists", return_value=False),
    ):
        import sys
        fake_psutil = _fake_psutil(total_ram=4 * 1024**3, vcpu=2)
        with patch.dict("sys.modules", {"psutil": fake_psutil}):
            caps = probe_host()

    assert isinstance(caps, HostCapabilities)
    assert caps.arch == "arm64"
    assert caps.total_vcpu == 2
