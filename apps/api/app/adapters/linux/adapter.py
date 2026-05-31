from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session

from app.adapters.aws.client import AWSClient
from app.adapters.aws.tags import device_tags
from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    SPI_VERSION,
)
from app.models import Device, DeviceTemplate

# Ubuntu 24.04 LTS SSM-enabled AMIs by region
_AMI_MAP: dict[str, str] = {
    "us-east-1": "ami-0c02fb55956c7d316",
    "us-east-2": "ami-097a2df4ac947655f",
    "us-west-1": "ami-0d9858aa3c6322f73",
    "us-west-2": "ami-098e42ae54c764c35",
    "eu-west-1": "ami-0d2a4a5d69e46ea0b",
    "eu-west-2": "ami-0f540e9f488cfa27d",
    "eu-central-1": "ami-0bd99ef9eccfee250",
    "ap-southeast-1": "ami-08569b978cc4dfa10",
    "ap-northeast-1": "ami-0dfa284c9d7b2adad",
}

_DEFAULT_INSTANCE_TYPE = "t3.medium"
_BOOTSTRAP_ROLE = "DeviceLab-RuntimeAgent"
_SG_NAME = "DeviceLab-Default"


@dataclass
class ProviderIds:
    instance_id: str
    region: str
    role_arn: str
    security_group_id: str


@dataclass
class LifecycleEvent:
    event_type: str
    timestamp: datetime
    message: str


class LinuxAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="linux",
            display_name="Linux (EC2 + SSM)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["click", "type", "key", "scroll", "raw_shell"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=True,
                dangerous_actions=["raw_shell"],
            ),
            required_providers=["aws_ec2", "ssm"],
        )

    async def observe(self, device: object, tier: str) -> object:
        from app.adapters.spi import CapabilityUnsupportedError
        if tier not in self.manifest().capabilities.observe:
            raise CapabilityUnsupportedError(tier, "linux")
        from app.services.observation import observe_device
        return await observe_device(device, tier)

    async def act(self, device: object, action: str, params: dict) -> object:
        from app.adapters.spi import CapabilityUnsupportedError
        if action not in self.manifest().capabilities.interact:
            raise CapabilityUnsupportedError(action, "linux")
        from app.services.interaction import act_on_device
        return await act_on_device(device, action, params)

    async def snapshot(self, device: object) -> object:
        from app.services.snapshots import create_snapshot
        return await create_snapshot(None, device.workspace_id, device.id)

    def __init__(self, client: AWSClient, region: str) -> None:
        self._client = client
        self._region = region

    def _get_ami(self) -> str:
        return _AMI_MAP.get(self._region, _AMI_MAP["us-east-1"])

    async def provision(self, device: Device, template: DeviceTemplate) -> ProviderIds:
        workspace_id = str(device.workspace_id)
        device_id = str(device.id)
        template_name = template.name

        role_arn = self._client.ensure_iam_role(
            _BOOTSTRAP_ROLE,
            {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }],
            },
            {},
        )

        sg_id = self._client.ensure_security_group(
            _SG_NAME,
            "DeviceLab default — no inbound",
        )

        tags = {t["Key"]: t["Value"] for t in device_tags(workspace_id, device_id, template_name)}
        instance_id = self._client.run_instance(
            image_id=self._get_ami(),
            instance_type=_DEFAULT_INSTANCE_TYPE,
            iam_instance_profile_arn=role_arn,
            security_group_id=sg_id,
            tags=tags,
        )

        return ProviderIds(
            instance_id=instance_id,
            region=self._region,
            role_arn=role_arn,
            security_group_id=sg_id,
        )

    async def wait_for_running(self, instance_id: str, timeout: int = 300) -> None:
        self._client.wait_for_instance_running(instance_id)

    async def bootstrap_agent(self, instance_id: str) -> None:
        commands = [
            "#!/bin/bash",
            "set -e",
            "apt-get update -qq && apt-get install -y python3.12 python3-pip || true",
            "pip3 install --quiet requests",
            # Agent script is embedded inline for phase 02
            "cat > /opt/devicelab-agent.py << 'AGENT_EOF'",
            "import time, os, urllib.request, json",
            "CONTROL_API = os.environ.get('DEVICELAB_API', '')",
            "DEVICE_ID = os.environ.get('DEVICELAB_DEVICE_ID', '')",
            "def heartbeat():",
            "    if not CONTROL_API: return",
            "    try:",
            "        req = urllib.request.Request(f'{CONTROL_API}/api/v1/devices/{DEVICE_ID}/heartbeat',",
            "            data=json.dumps({'status': 'alive'}).encode(), method='POST',",
            "            headers={'Content-Type': 'application/json'})",
            "        urllib.request.urlopen(req, timeout=5)",
            "    except Exception: pass",
            "heartbeat()",
            "print('DeviceLab agent started')",
            "while True:",
            "    heartbeat()",
            "    time.sleep(30)",
            "AGENT_EOF",
            "python3 /opt/devicelab-agent.py &",
        ]
        self._client.send_ssm_command(instance_id, commands)

    async def terminate(self, device: Device) -> None:
        if not device.provider_ids_json:
            return
        ids = json.loads(device.provider_ids_json)
        if instance_id := ids.get("instance_id"):
            self._client.terminate_instance(instance_id)

    def get_lifecycle_events(self, instance_id: str) -> list[LifecycleEvent]:
        return [
            LifecycleEvent(
                event_type="instance_created",
                timestamp=datetime.now(UTC),
                message=f"EC2 instance {instance_id} created",
            )
        ]
