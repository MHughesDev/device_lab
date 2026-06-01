# test_doctor.py — devicelab doctor unit tests (Task 07-16)
from __future__ import annotations
from unittest.mock import MagicMock, patch
import subprocess

import pytest

from app.cli.doctor import (
    CheckResult,
    _check_adb,
    _check_disk_space,
    _check_docker,
    _check_ports,
    _check_qemu,
    run_doctor,
)


def test_check_docker_ok_when_daemon_running():
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch(
            "subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ),
    ):
        result = _check_docker()
    assert result.status == "ok"
    assert result.name == "Docker"


def test_check_docker_fail_when_cli_missing():
    with patch("shutil.which", return_value=None):
        result = _check_docker()
    assert result.status == "fail"
    assert "not found" in result.message


def test_check_docker_fail_when_daemon_not_running():
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch(
            "subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="Cannot connect"),
        ),
    ):
        result = _check_docker()
    assert result.status == "fail"
    assert "daemon" in result.message.lower()


def test_check_disk_space_ok_when_plenty():
    fake_usage = MagicMock()
    fake_usage.free = 50 * 1024 ** 3  # 50 GB
    with patch("psutil.disk_usage", return_value=fake_usage):
        result = _check_disk_space()
    assert result.status == "ok"
    assert "50.0 GB" in result.message


def test_check_disk_space_fail_when_critically_low():
    fake_usage = MagicMock()
    fake_usage.free = 1 * 1024 ** 3  # 1 GB
    with patch("psutil.disk_usage", return_value=fake_usage):
        result = _check_disk_space()
    assert result.status == "fail"
    assert result.remedy != ""


def test_check_adb_warn_when_missing():
    with patch("shutil.which", return_value=None):
        result = _check_adb()
    assert result.status == "warn"
    assert "adb" in result.message.lower()


def test_check_adb_ok_when_present():
    with (
        patch("shutil.which", return_value="/usr/local/bin/adb"),
        patch(
            "subprocess.run",
            return_value=MagicMock(returncode=0, stdout="Android Debug Bridge version 1.0.41\n"),
        ),
    ):
        result = _check_adb()
    assert result.status == "ok"


def test_check_ports_ok_when_free():
    with patch("socket.socket") as mock_sock_class:
        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect_ex.return_value = 1  # not in use
        mock_sock_class.return_value = mock_sock
        result = _check_ports()
    assert result.status == "ok"


def test_check_ports_fail_when_occupied():
    with patch("socket.socket") as mock_sock_class:
        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect_ex.return_value = 0  # port in use
        mock_sock_class.return_value = mock_sock
        result = _check_ports()
    assert result.status == "fail"
    assert "already in use" in result.message


def test_run_doctor_returns_list_of_check_results():
    with (
        patch("shutil.which", return_value=None),
        patch("psutil.disk_usage", return_value=MagicMock(free=20 * 1024 ** 3)),
        patch("socket.socket") as mock_sock_class,
    ):
        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect_ex.return_value = 1
        mock_sock_class.return_value = mock_sock
        results = run_doctor()

    assert isinstance(results, list)
    assert all(isinstance(r, CheckResult) for r in results)
    assert len(results) >= 5
