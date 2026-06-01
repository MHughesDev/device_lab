# test_adb_channel.py — ADBChannel unit tests (Task 07-11)
from __future__ import annotations
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from app.transport.adb import ADBChannel
from app.transport.channel import ExecResult


def _make_channel(serial: str = "emulator-5554") -> ADBChannel:
    return ADBChannel(serial)


def _cp(returncode: int = 0, stdout: str = "", stderr: str = "") -> CompletedProcess:
    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


@pytest.mark.asyncio
async def test_adb_channel_exec_returns_stdout_and_exit_code():
    channel = _make_channel()
    with patch("subprocess.run", return_value=_cp(stdout="hello\n")):
        result = await channel.exec("echo hello")
    assert isinstance(result, ExecResult)
    assert result.stdout == "hello\n"
    assert result.exit_code == 0


@pytest.mark.asyncio
async def test_adb_channel_exec_nonzero_exit_code():
    channel = _make_channel()
    with patch("subprocess.run", return_value=_cp(returncode=1, stderr="not found")):
        result = await channel.exec("badcmd")
    assert result.exit_code == 1
    assert "not found" in result.stderr


@pytest.mark.asyncio
async def test_adb_channel_exec_list_joins_with_and():
    channel = _make_channel()
    captured: list[list] = []

    def fake_run(args, **kwargs):
        captured.append(args)
        return _cp()

    with patch("subprocess.run", side_effect=fake_run):
        await channel.exec(["cmd1", "cmd2"])

    # args[4] is the shell_cmd passed to adb shell
    assert "cmd1 && cmd2" == captured[0][4]


@pytest.mark.asyncio
async def test_adb_channel_heartbeat_true_when_device_online():
    channel = _make_channel()
    with patch("subprocess.run", return_value=_cp(stdout="device\n")):
        alive = await channel.heartbeat()
    assert alive is True


@pytest.mark.asyncio
async def test_adb_channel_heartbeat_false_when_offline():
    channel = _make_channel()
    with patch("subprocess.run", return_value=_cp(returncode=1, stderr="no devices found")):
        alive = await channel.heartbeat()
    assert alive is False
