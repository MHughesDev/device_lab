# test_ssh_channel.py — SSHChannel unit tests (Task 07-12)
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.transport.channel import ExecResult
from app.transport.ssh import SSHChannel


def _make_channel() -> SSHChannel:
    return SSHChannel("127.0.0.1", port=15900, username="Administrator")


def _mock_run_result(stdout: str = "", stderr: str = "", exit_status: int = 0) -> MagicMock:
    r = MagicMock()
    r.stdout = stdout
    r.stderr = stderr
    r.exit_status = exit_status
    return r


@pytest.mark.asyncio
async def test_ssh_channel_exec_returns_stdout_and_exit_code():
    channel = _make_channel()
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=_mock_run_result(stdout="hello from windows\n"))

    with patch.object(channel, "_connect", AsyncMock(return_value=mock_conn)):
        result = await channel.exec("echo hello")

    assert isinstance(result, ExecResult)
    assert "hello" in result.stdout
    assert result.exit_code == 0


@pytest.mark.asyncio
async def test_ssh_channel_exec_nonzero_exit_code():
    channel = _make_channel()
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=_mock_run_result(stderr="command not found", exit_status=1))

    with patch.object(channel, "_connect", AsyncMock(return_value=mock_conn)):
        result = await channel.exec("badcmd")

    assert result.exit_code == 1
    assert "command not found" in result.stderr


@pytest.mark.asyncio
async def test_ssh_channel_exec_list_joins_with_and():
    channel = _make_channel()
    captured: list[str] = []

    async def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return _mock_run_result()

    mock_conn = AsyncMock()
    mock_conn.run = fake_run

    with patch.object(channel, "_connect", AsyncMock(return_value=mock_conn)):
        await channel.exec(["cmd1", "cmd2"])

    assert "cmd1 && cmd2" in captured[0]


@pytest.mark.asyncio
async def test_ssh_channel_heartbeat_true_when_connected():
    channel = _make_channel()
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=_mock_run_result(stdout="ok"))

    with patch.object(channel, "_connect", AsyncMock(return_value=mock_conn)):
        alive = await channel.heartbeat()

    assert alive is True


@pytest.mark.asyncio
async def test_ssh_channel_heartbeat_false_on_connection_error():
    channel = _make_channel()

    with patch.object(channel, "_connect", AsyncMock(side_effect=OSError("Connection refused"))):
        alive = await channel.heartbeat()

    assert alive is False
