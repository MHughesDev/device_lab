# test_conformance.py — Parametrized conformance tests for all DeviceAdapter implementations
# Task 07-10: Linux conformance suite is parametrized over location ∈ {cloud, local}.
from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch

from app.adapters.spi import (
    SUPPORTED_SPI_VERSIONS,
    CapabilityUnsupportedError,
    DeviceCapabilities,
)
from app.adapters.linux.adapter import LinuxAdapter
from app.adapters.android.adapter import AndroidAdapter
from app.adapters.macos.adapter import MacOSAdapter
from app.adapters.windows.adapter import WindowsAdapter
from app.adapters.ios_sim.adapter import IOSSimulatorAdapter
from tests.adapters.conformance.fixtures import FakeDevice, FakeLocalDevice, FakeTemplate

_ALL_ADAPTERS = [LinuxAdapter, AndroidAdapter, MacOSAdapter, WindowsAdapter, IOSSimulatorAdapter]


# ---------------------------------------------------------------------------
# SPI contract tests (all adapters)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
def test_manifest_valid(adapter_class):
    m = adapter_class.manifest()
    assert m.spi_version in SUPPORTED_SPI_VERSIONS
    assert isinstance(m.family, str) and m.family
    assert isinstance(m.capabilities, DeviceCapabilities)


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
def test_manifest_family_matches_register(adapter_class):
    from app.adapters.registry import AdapterRegistry
    AdapterRegistry.reset()
    AdapterRegistry.register(adapter_class)
    m = adapter_class.manifest()
    assert AdapterRegistry.get(m.family) is adapter_class
    AdapterRegistry.reset()


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
@pytest.mark.asyncio
async def test_observe_unsupported_tier_raises(adapter_class):
    adapter = object.__new__(adapter_class)
    device = FakeDevice(family=adapter_class.manifest().family)
    with pytest.raises(CapabilityUnsupportedError):
        await adapter.observe(device, "vlm_unsupported_tier_xyz")


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
@pytest.mark.asyncio
async def test_act_unsupported_action_raises(adapter_class):
    adapter = object.__new__(adapter_class)
    device = FakeDevice(family=adapter_class.manifest().family)
    with pytest.raises(CapabilityUnsupportedError):
        await adapter.act(device, "unsupported_action_xyz", {})


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
@pytest.mark.asyncio
async def test_capability_unsupported_error_type(adapter_class):
    """Unsupported capabilities must always raise CapabilityUnsupportedError."""
    adapter = object.__new__(adapter_class)
    device = FakeDevice(family=adapter_class.manifest().family)
    raised = None
    try:
        await adapter.observe(device, "vlm_unsupported_tier_xyz")
    except CapabilityUnsupportedError as e:
        raised = e
    except NotImplementedError:
        pytest.fail("Adapter raised NotImplementedError instead of CapabilityUnsupportedError")
    assert isinstance(raised, CapabilityUnsupportedError)


# ---------------------------------------------------------------------------
# Channel factory tests (Task 07-01 / 07-10)
# ---------------------------------------------------------------------------

def test_channel_factory_resolves_ssm_for_cloud():
    from app.transport.channel import ChannelFactory
    from app.transport.ssm import SSMChannel
    device = FakeDevice(family="linux", location="cloud")
    channel = ChannelFactory.get(device)
    assert isinstance(channel, SSMChannel)


def test_channel_factory_resolves_ssm_powershell_for_windows():
    from app.transport.channel import ChannelFactory
    from app.transport.ssm import SSMChannel
    device = FakeDevice(family="windows", location="cloud")
    channel = ChannelFactory.get(device)
    assert isinstance(channel, SSMChannel)
    assert channel._document == "AWS-RunPowerShellScript"


def test_channel_factory_resolves_docker_for_local_linux():
    from app.transport.channel import ChannelFactory
    from app.transport.docker_exec import DockerExecChannel

    mock_docker_client = MagicMock()
    mock_container = MagicMock()
    mock_docker_client.containers.get.return_value = mock_container

    with patch("docker.from_env", return_value=mock_docker_client):
        device = FakeLocalDevice(family="linux")
        channel = ChannelFactory.get(device)
    assert isinstance(channel, DockerExecChannel)


def test_device_defaults_to_cloud_location():
    device = FakeDevice()
    assert device.location == "cloud"


# ---------------------------------------------------------------------------
# Linux adapter: location-parametrized provisioning contract (Task 07-10)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("location", ["cloud", "local"])
async def test_linux_provision_returns_provider_ids(location):
    """provision() must return a non-empty provider_ids dict for both locations."""
    device = FakeDevice(family="linux", location=location)
    template = FakeTemplate(family="linux")

    if location == "cloud":
        from app.adapters.aws.client import AWSClient
        mock_client = MagicMock(spec=AWSClient)
        mock_client.ensure_iam_role.return_value = "arn:aws:iam::123456789012:role/fake"
        mock_client.ensure_security_group.return_value = "sg-fake"
        mock_client.run_instance.return_value = "i-fake123"
        adapter = LinuxAdapter(client=mock_client, region="us-east-1")
        result = await adapter.provision(device, template)
        # Cloud path returns a ProviderIds dataclass
        import dataclasses
        assert dataclasses.is_dataclass(result) or isinstance(result, dict)
    else:
        mock_docker_client = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "abc123containerid"
        mock_docker_client.containers.run.return_value = mock_container

        with patch("docker.from_env", return_value=mock_docker_client):
            from app.adapters.linux.local_provision import provision as local_provision
            result = await local_provision(device, template)
        assert result.get("container_id") == "abc123containerid"


@pytest.mark.asyncio
@pytest.mark.parametrize("location", ["cloud", "local"])
async def test_linux_terminate_is_idempotent(location):
    """terminate() must not raise even when provider resources are already gone."""
    if location == "cloud":
        from app.adapters.aws.client import AWSClient
        mock_client = MagicMock(spec=AWSClient)
        adapter = LinuxAdapter(client=mock_client, region="us-east-1")
        # device with no provider_ids_json
        device = FakeDevice(family="linux", location="cloud", provider_ids_json="{}")
        await adapter.terminate(device)
    else:
        mock_docker_client = MagicMock()
        mock_docker_client.containers.get.side_effect = Exception("Not Found")
        with patch("docker.from_env", return_value=mock_docker_client):
            from app.adapters.linux.local_provision import terminate as local_terminate
            device = FakeLocalDevice(family="linux")
            await local_terminate(device)  # must not raise
