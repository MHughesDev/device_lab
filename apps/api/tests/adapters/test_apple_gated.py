# test_apple_gated.py — Apple-gated local provisioner tests (Task 07-13)
from __future__ import annotations
from unittest.mock import patch

import pytest

from app.services.local.host_probe import HostCapabilities
from app.services.local.placement import PlacementError


def _caps(is_apple: bool, os: str = "linux") -> HostCapabilities:
    return HostCapabilities(
        os=os,
        arch="x86_64",
        docker_available=True,
        virtualization_available=True,
        is_apple_hardware=is_apple,
        total_ram_mb=16384,
        total_vcpu=8,
        free_disk_mb=100_000,
    )


@pytest.mark.asyncio
async def test_macos_local_provision_refuses_on_non_apple():
    from app.adapters.macos.local_provision import provision

    device = object()
    template = object()

    with patch("app.adapters.macos.local_provision.probe_host", return_value=_caps(is_apple=False)):
        with pytest.raises(PlacementError, match="Apple hardware"):
            await provision(device, template)


@pytest.mark.asyncio
async def test_ios_sim_local_provision_refuses_on_non_apple():
    from app.adapters.ios_sim.local_provision import provision

    device = object()
    template = object()

    with patch("app.adapters.ios_sim.local_provision.probe_host", return_value=_caps(is_apple=False)):
        with pytest.raises(PlacementError, match="Apple hardware"):
            await provision(device, template)


def test_local_shell_channel_heartbeat_always_true():
    """LocalShellChannel.heartbeat() is always True — local host is always reachable."""
    import asyncio
    from app.transport.local_shell import LocalShellChannel

    channel = LocalShellChannel()
    result = asyncio.get_event_loop().run_until_complete(channel.heartbeat())
    assert result is True


@pytest.mark.asyncio
async def test_local_shell_channel_exec_returns_stdout():
    from unittest.mock import patch
    from subprocess import CompletedProcess
    from app.transport.local_shell import LocalShellChannel

    channel = LocalShellChannel()
    mock_result = CompletedProcess(args=[], returncode=0, stdout="hello\n", stderr="")
    with patch("subprocess.run", return_value=mock_result):
        result = await channel.exec("echo hello")

    assert result.stdout == "hello\n"
    assert result.exit_code == 0


@pytest.mark.asyncio
async def test_channel_factory_returns_local_shell_for_ios_sim():
    """ChannelFactory resolves ios_sim+local to LocalShellChannel."""
    from unittest.mock import MagicMock
    from app.transport.channel import ChannelFactory
    from app.transport.local_shell import LocalShellChannel

    device = MagicMock()
    device.family = "ios_sim"
    device.location = "local"
    device.provider_ids_json = "{}"

    channel = ChannelFactory.get(device)
    assert isinstance(channel, LocalShellChannel)


@pytest.mark.asyncio
async def test_channel_factory_returns_ssh_for_macos_local():
    """ChannelFactory resolves macos+local to SSHChannel."""
    from unittest.mock import MagicMock
    from app.transport.channel import ChannelFactory
    from app.transport.ssh import SSHChannel

    device = MagicMock()
    device.family = "macos"
    device.location = "local"
    device.provider_ids_json = '{"vm_ip": "127.0.0.1", "ssh_port": 16001, "ssh_username": "user"}'

    channel = ChannelFactory.get(device)
    assert isinstance(channel, SSHChannel)
