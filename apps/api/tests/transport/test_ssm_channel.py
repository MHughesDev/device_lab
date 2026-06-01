# test_ssm_channel.py — SSMChannel unit tests (Tasks 07-01, 07-02)
from __future__ import annotations
from unittest.mock import MagicMock, patch

import pytest

from app.transport.channel import ExecResult
from app.transport.ssm import SSMChannel


def _make_channel(document: str = "AWS-RunShellScript") -> tuple[SSMChannel, MagicMock]:
    """Return (channel, mock_ssm_client) with boto3 patched."""
    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client):
        channel = SSMChannel("i-fake", "us-east-1", document=document)
    channel._client = mock_client
    return channel, mock_client


@pytest.mark.asyncio
async def test_ssm_channel_exec_polls_until_success():
    channel, mock_client = _make_channel()

    mock_client.send_command.return_value = {"Command": {"CommandId": "cmd-123"}}
    mock_client.get_command_invocation.return_value = {
        "Status": "Success",
        "StandardOutputContent": "hello",
        "StandardErrorContent": "",
        "ResponseCode": 0,
    }

    result = await channel.exec("echo hello")

    assert isinstance(result, ExecResult)
    assert result.stdout == "hello"
    assert result.exit_code == 0
    mock_client.send_command.assert_called_once()
    mock_client.get_command_invocation.assert_called()


@pytest.mark.asyncio
async def test_ssm_channel_exec_surfaces_failed_status():
    channel, mock_client = _make_channel()

    mock_client.send_command.return_value = {"Command": {"CommandId": "cmd-456"}}
    mock_client.get_command_invocation.return_value = {
        "Status": "Failed",
        "StandardOutputContent": "",
        "StandardErrorContent": "command not found",
        "ResponseCode": 127,
    }

    result = await channel.exec("nonexistent_cmd")

    assert result.exit_code == 127
    assert "command not found" in result.stderr


@pytest.mark.asyncio
async def test_ssm_channel_exec_timeout_returns_sentinel():
    """If the command never reaches terminal state, exec returns exit_code=-1."""
    channel, mock_client = _make_channel()

    mock_client.send_command.return_value = {"Command": {"CommandId": "cmd-789"}}
    # Always InProgress — simulates timeout
    mock_client.get_command_invocation.return_value = {
        "Status": "InProgress",
        "StandardOutputContent": "",
        "StandardErrorContent": "",
        "ResponseCode": -1,
    }

    # Use a very short timeout so the test finishes quickly
    result = await channel.exec("sleep 999", timeout_ms=100)

    assert result.exit_code == -1
    assert "Timeout" in result.stderr


@pytest.mark.asyncio
async def test_ssm_channel_uses_powershell_document_for_windows():
    channel, mock_client = _make_channel(document="AWS-RunPowerShellScript")

    mock_client.send_command.return_value = {"Command": {"CommandId": "ps-cmd"}}
    mock_client.get_command_invocation.return_value = {
        "Status": "Success",
        "StandardOutputContent": "OK",
        "StandardErrorContent": "",
        "ResponseCode": 0,
    }

    await channel.exec("Write-Output OK")

    call_kwargs = mock_client.send_command.call_args
    assert call_kwargs[1]["DocumentName"] == "AWS-RunPowerShellScript"


@pytest.mark.asyncio
async def test_ssm_channel_exec_list_of_commands():
    """A list of commands should be forwarded as-is to SSM."""
    channel, mock_client = _make_channel()

    mock_client.send_command.return_value = {"Command": {"CommandId": "multi-cmd"}}
    mock_client.get_command_invocation.return_value = {
        "Status": "Success",
        "StandardOutputContent": "b64data",
        "StandardErrorContent": "",
        "ResponseCode": 0,
    }

    await channel.exec(["cmd1", "cmd2"])

    call_kwargs = mock_client.send_command.call_args
    assert call_kwargs[1]["Parameters"]["commands"] == ["cmd1", "cmd2"]
