# adapter.py — Windows adapter: EC2 Windows Server + SSM + UIA observation
from __future__ import annotations
import json

from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    CapabilityUnsupportedError,
    SPI_VERSION,
)


class WindowsAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="windows",
            display_name="Windows Server (EC2 + SSM)",
            capabilities=DeviceCapabilities(
                observe=["screenshot", "ax_tree"],
                interact=["click", "double_click", "right_click", "mouse_move",
                          "drag", "scroll", "cursor_position", "type", "key"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=True,
                screen_recording=True,
            ),
            required_providers=["aws_ec2", "ssm"],
        )

    async def provision(self, device: object, template: object) -> dict:
        """
        Launch EC2 Windows Server 2022 AMI.
        SSM bootstrap: install Python 3.12, runtime agent, enable UIA.
        """
        import boto3
        workspace_id = str(getattr(device, "workspace_id", ""))
        device_id = str(getattr(device, "id", ""))

        ec2 = boto3.client("ec2", region_name="us-east-1")
        images = ec2.describe_images(
            Filters=[
                {"Name": "name", "Values": ["Windows_Server-2022-English-Full-Base-*"]},
                {"Name": "state", "Values": ["available"]},
            ],
            Owners=["amazon"],
        )
        ami_id = sorted(images["Images"], key=lambda i: i["CreationDate"], reverse=True)[0]["ImageId"]

        resp = ec2.run_instances(
            ImageId=ami_id,
            InstanceType="t3.large",
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "DeviceLab:Workspace", "Value": workspace_id},
                    {"Key": "DeviceLab:Device", "Value": device_id},
                    {"Key": "DeviceLab:Family", "Value": "windows"},
                ],
            }],
        )
        instance_id = resp["Instances"][0]["InstanceId"]

        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={"commands": [
                "Install-Module -Name PythonInstaller -Force -ErrorAction SilentlyContinue",
                "pip install devicelab-agent --quiet",
                "Enable-WindowsOptionalFeature -Online -FeatureName NetFx3 -All",
            ]},
        )

        return {"instance_id": instance_id, "region": "us-east-1"}

    async def terminate(self, device: object) -> None:
        if not getattr(device, "provider_ids_json", None):
            return
        ids = json.loads(device.provider_ids_json)  # type: ignore[attr-defined]
        instance_id = ids.get("instance_id")
        if instance_id:
            import boto3
            ec2 = boto3.client("ec2", region_name=ids.get("region", "us-east-1"))
            ec2.terminate_instances(InstanceIds=[instance_id])

    async def observe(self, device: object, tier: str) -> object:
        from app.adapters.windows.observation import observe_windows
        return await observe_windows(device, tier)

    async def act(self, device: object, action: str, params: dict) -> object:
        from app.adapters.windows.interaction import act_windows
        return await act_windows(device, action, params)
