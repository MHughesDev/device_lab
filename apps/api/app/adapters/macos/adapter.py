# adapter.py — macOS adapter: EC2 mac2.metal Dedicated Host + SSM + AX observation
from __future__ import annotations
import json
import logging
from datetime import UTC, datetime, timedelta

from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    CapabilityUnsupportedError,
    SPI_VERSION,
)

log = logging.getLogger(__name__)


class MacOSAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="macos",
            display_name="macOS (EC2 mac2.metal Dedicated Host)",
            capabilities=DeviceCapabilities(
                observe=["screenshot", "ax_tree"],
                interact=["click", "double_click", "right_click", "mouse_move",
                          "drag", "scroll", "cursor_position", "type", "key"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=False,
                screen_recording=True,
            ),
            required_providers=["aws_ec2_dedicated_host", "ssm"],
        )

    async def provision(self, device: object, template: object) -> dict:
        """Allocate EC2 Dedicated Host (mac2.metal), launch Mac instance, bootstrap agent."""
        import boto3
        workspace_id = str(getattr(device, "workspace_id", ""))
        device_id = str(getattr(device, "id", ""))
        region = "us-east-1"

        ec2 = boto3.client("ec2", region_name=region)

        # Allocate dedicated host — 24h minimum billing applies
        host_resp = ec2.allocate_hosts(
            InstanceType="mac2.metal",
            Quantity=1,
            AvailabilityZone=f"{region}a",
            AutoPlacement="on",
            TagSpecifications=[{
                "ResourceType": "dedicated-host",
                "Tags": [
                    {"Key": "DeviceLab:Workspace", "Value": workspace_id},
                    {"Key": "DeviceLab:Device", "Value": device_id},
                ],
            }],
        )
        host_id = host_resp["HostIds"][0]

        images = ec2.describe_images(
            Filters=[
                {"Name": "name", "Values": ["amzn-ec2-macos-*arm64*"]},
                {"Name": "state", "Values": ["available"]},
            ],
            Owners=["amazon"],
        )
        ami_id = sorted(images["Images"], key=lambda i: i["CreationDate"], reverse=True)[0]["ImageId"]

        resp = ec2.run_instances(
            ImageId=ami_id,
            InstanceType="mac2.metal",
            MinCount=1,
            MaxCount=1,
            Placement={"HostId": host_id},
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "DeviceLab:Workspace", "Value": workspace_id},
                    {"Key": "DeviceLab:Device", "Value": device_id},
                    {"Key": "DeviceLab:Family", "Value": "macos"},
                ],
            }],
        )
        instance_id = resp["Instances"][0]["InstanceId"]

        return {"instance_id": instance_id, "host_id": host_id, "region": region,
                "host_allocated_at": datetime.now(UTC).isoformat()}

    async def terminate(self, device: object) -> None:
        """Terminate instance. Warn if dedicated host < 24h old (still billed)."""
        if not getattr(device, "provider_ids_json", None):
            return
        ids = json.loads(device.provider_ids_json)  # type: ignore[attr-defined]
        instance_id = ids.get("instance_id")
        host_allocated_at = ids.get("host_allocated_at")
        region = ids.get("region", "us-east-1")

        if host_allocated_at:
            allocated = datetime.fromisoformat(host_allocated_at)
            age = datetime.now(UTC) - allocated
            if age < timedelta(hours=24):
                log.warning(
                    "Dedicated Host allocated %.1fh ago — 24h minimum billing still applies",
                    age.total_seconds() / 3600,
                )

        if instance_id:
            import boto3
            ec2 = boto3.client("ec2", region_name=region)
            ec2.terminate_instances(InstanceIds=[instance_id])

    async def observe(self, device: object, tier: str) -> object:
        from app.adapters.macos.observation import observe_macos
        return await observe_macos(device, tier)

    async def act(self, device: object, action: str, params: dict) -> object:
        from app.adapters.macos.interaction import act_macos
        return await act_macos(device, action, params)
