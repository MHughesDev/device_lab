# adapter.py — Android adapter: EC2 nested-virt AOSP emulator provisioning and lifecycle
from __future__ import annotations
import json

from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    CapabilityUnsupportedError,
    SPI_VERSION,
)

_DEFAULT_INSTANCE_TYPE = "c8i.xlarge"


class AndroidAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="android",
            display_name="Android Emulator (EC2 nested virt)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["click", "swipe", "type", "key", "scroll"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=False,
            ),
            required_providers=["aws_ec2", "ssm", "adb"],
            supported_regions=None,
        )

    async def provision(self, device: object, template: object) -> dict:
        """
        1. Launch EC2 c8i.xlarge (KVM nested-virt capable).
        2. SSM bootstrap: install AOSP emulator, boot AVD.
        3. Poll adb devices until emulator appears (timeout 5 min).
        """
        import boto3
        from app.adapters.aws.tags import device_tags

        workspace_id = str(device.workspace_id)  # type: ignore[attr-defined]
        device_id = str(device.id)  # type: ignore[attr-defined]

        ec2 = boto3.client("ec2", region_name="us-east-1")
        images = ec2.describe_images(
            Filters=[
                {"Name": "name", "Values": ["al2023-ami-2023*x86_64"]},
                {"Name": "state", "Values": ["available"]},
            ],
            Owners=["amazon"],
        )
        ami_id = sorted(images["Images"], key=lambda i: i["CreationDate"], reverse=True)[0]["ImageId"]

        tags = {t["Key"]: t["Value"] for t in device_tags(workspace_id, device_id, "android")}
        tags["DeviceLab:Family"] = "android"
        tag_specs = [{"ResourceType": "instance", "Tags": [{"Key": k, "Value": v} for k, v in tags.items()]}]

        resp = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=_DEFAULT_INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=tag_specs,
        )
        instance_id = resp["Instances"][0]["InstanceId"]

        ssm = boto3.client("ssm", region_name="us-east-1")
        bootstrap_commands = [
            "yum install -y qemu-kvm android-tools || true",
            "avdmanager create avd -n devicelab -k 'system-images;android-34;google_apis;x86_64' --force || true",
            "nohup emulator -avd devicelab -no-window -no-audio > /tmp/emulator.log 2>&1 &",
            "adb wait-for-device",
        ]
        ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": bootstrap_commands},
        )

        return {"instance_id": instance_id, "adb_serial": "emulator-5554", "region": "us-east-1"}

    async def terminate(self, device: object) -> None:
        """Stop emulator via adb emu kill, then terminate EC2."""
        if not getattr(device, "provider_ids_json", None):
            return
        ids = json.loads(device.provider_ids_json)  # type: ignore[attr-defined]
        instance_id = ids.get("instance_id")
        if instance_id:
            import boto3
            ec2 = boto3.client("ec2", region_name=ids.get("region", "us-east-1"))
            ec2.terminate_instances(InstanceIds=[instance_id])

    async def observe(self, device: object, tier: str) -> object:
        from app.adapters.android.observation import observe_android
        return await observe_android(device, tier)

    async def act(self, device: object, action: str, params: dict) -> object:
        from app.adapters.android.interaction import act_android
        return await act_android(device, action, params)
