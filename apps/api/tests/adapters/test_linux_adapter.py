import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.linux.adapter import LinuxAdapter, ProviderIds
from app.models import Device, DeviceTemplate


def _make_device(state: str = "provisioning") -> Device:
    return Device(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        template_id=uuid.uuid4(),
        family="linux",
        state=state,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_template() -> DeviceTemplate:
    return DeviceTemplate(
        id=uuid.uuid4(),
        family="linux",
        name="linux-default",
    )


class TestLinuxAdapter:
    def _adapter(self) -> tuple[LinuxAdapter, MagicMock]:
        client = MagicMock()
        client.ensure_iam_role.return_value = "arn:aws:iam::123:role/test"
        client.ensure_security_group.return_value = "sg-abc123"
        client.run_instance.return_value = "i-abc123"
        client.send_ssm_command.return_value = "cmd-abc"
        return LinuxAdapter(client, "us-east-1"), client

    @pytest.mark.asyncio
    async def test_provision_returns_provider_ids(self) -> None:
        adapter, client = self._adapter()
        device = _make_device()
        template = _make_template()
        ids = await adapter.provision(device, template)
        assert ids.instance_id == "i-abc123"
        assert ids.region == "us-east-1"
        client.run_instance.assert_called_once()

    @pytest.mark.asyncio
    async def test_provision_tags_instance(self) -> None:
        adapter, client = self._adapter()
        device = _make_device()
        template = _make_template()
        await adapter.provision(device, template)
        call_kwargs = client.run_instance.call_args[1]
        tags = call_kwargs["tags"]
        assert "DeviceLab:ManagedBy" in tags
        assert "DeviceLab:Device" in tags
        assert tags["DeviceLab:Device"] == str(device.id)

    @pytest.mark.asyncio
    async def test_terminate_calls_terminate_instance(self) -> None:
        adapter, client = self._adapter()
        device = _make_device("ready")
        device.provider_ids_json = json.dumps({"instance_id": "i-abc123"})
        await adapter.terminate(device)
        client.terminate_instance.assert_called_once_with("i-abc123")

    @pytest.mark.asyncio
    async def test_terminate_no_provider_ids_is_noop(self) -> None:
        adapter, client = self._adapter()
        device = _make_device("ready")
        device.provider_ids_json = None
        await adapter.terminate(device)
        client.terminate_instance.assert_not_called()

    @pytest.mark.asyncio
    async def test_bootstrap_agent_sends_ssm(self) -> None:
        adapter, client = self._adapter()
        await adapter.bootstrap_agent("i-abc123")
        client.send_ssm_command.assert_called_once()
        args = client.send_ssm_command.call_args
        assert args[0][0] == "i-abc123"
        assert len(args[0][1]) > 0


def test_manifest_spi_version():
    from app.adapters.spi import SPI_VERSION
    assert LinuxAdapter.manifest().spi_version == SPI_VERSION


def test_manifest_family():
    assert LinuxAdapter.manifest().family == "linux"


def test_manifest_snapshot_capable():
    assert LinuxAdapter.manifest().capabilities.snapshot is True
