# adapter.py — iOS Simulator adapter: macOS Dedicated Host + xcrun simctl lifecycle
from __future__ import annotations
import json

from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    CapabilityUnsupportedError,
    SPI_VERSION,
)


class IOSSimulatorAdapter(DeviceAdapter):
    """Inherits macOS Dedicated Host; adds simulator-specific lifecycle via xcrun simctl."""

    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="ios_sim",
            display_name="iOS Simulator (macOS EC2 + xcrun simctl)",
            capabilities=DeviceCapabilities(
                observe=["screenshot"],
                # drag = touch swipe; right_click/mouse_move/cursor_position not applicable on simulator
                interact=["click", "double_click", "drag", "scroll", "type", "key"],
                network=[],
                streaming=True,
                snapshot=True,
                screen_recording=True,
            ),
            required_providers=["aws_ec2_dedicated_host", "ssm"],
        )

    async def provision(self, device: object, template: object) -> dict:
        """Provision macOS host, create and boot iOS Simulator via xcrun simctl."""
        from app.adapters.macos.adapter import MacOSAdapter
        from app.transport.ssm import SSMChannel

        macos = MacOSAdapter()
        ids = await macos.provision(device, template)
        instance_id = ids["instance_id"]
        region = ids.get("region", "us-east-1")

        channel = SSMChannel(instance_id, region)
        await channel.exec([
            "xcrun simctl create devicelab-sim 'iPhone 15' 'iOS17.0' 2>/tmp/simctl.log",
            "UDID=$(xcrun simctl list devices | grep devicelab-sim | grep -o '[A-Z0-9-]*' | head -1)",
            "xcrun simctl boot $UDID",
            "echo $UDID > /tmp/sim_udid",
        ], timeout_ms=120_000)

        ids["sim_udid"] = "pending"
        return ids

    async def terminate(self, device: object) -> None:
        """Shutdown and delete simulator, then terminate macOS host."""
        if not getattr(device, "provider_ids_json", None):
            return
        ids = json.loads(device.provider_ids_json)  # type: ignore[attr-defined]
        instance_id = ids.get("instance_id")
        sim_udid = ids.get("sim_udid", "")
        region = ids.get("region", "us-east-1")

        if instance_id and sim_udid and sim_udid != "pending":
            from app.transport.ssm import SSMChannel
            channel = SSMChannel(instance_id, region)
            await channel.exec([
                f"xcrun simctl shutdown {sim_udid}",
                f"xcrun simctl delete {sim_udid}",
            ])

        if instance_id:
            import boto3
            ec2 = boto3.client("ec2", region_name=region)
            ec2.terminate_instances(InstanceIds=[instance_id])

    async def observe(self, device: object, tier: str) -> object:
        if tier not in self.manifest().capabilities.observe:
            raise CapabilityUnsupportedError(tier, "ios_sim")
        ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        sim_udid = ids.get("sim_udid", "")

        from datetime import UTC, datetime
        from app.models import ObservationEnvelope
        from app.transport.channel import ChannelFactory

        channel = ChannelFactory.get(device)
        result = await channel.exec([
            f"xcrun simctl io {sim_udid} screenshot /tmp/sim_screenshot.png",
            "base64 /tmp/sim_screenshot.png",
        ])
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="screenshot",
            screenshot_ref=result.stdout.strip(),
            observed_at=datetime.now(UTC),
        )

    async def act(self, device: object, action: str, params: dict) -> object:
        from app.adapters.ios_sim.interaction import act_ios_sim
        return await act_ios_sim(device, action, params)

    async def snapshot(self, device: object) -> object:
        """Clone simulator via xcrun simctl clone."""
        ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        instance_id = ids.get("instance_id", "")
        sim_udid = ids.get("sim_udid", "")
        region = ids.get("region", "us-east-1")
        from datetime import UTC, datetime
        snap_name = f"devicelab-snap-{int(datetime.now(UTC).timestamp())}"

        from app.transport.ssm import SSMChannel
        channel = SSMChannel(instance_id, region)
        await channel.exec(f"xcrun simctl clone {sim_udid} {snap_name}")
        return {"snapshot_name": snap_name}
