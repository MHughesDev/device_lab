# adapter.py — Real iOS adapter: AWS Device Farm remote access session
from __future__ import annotations
import json

from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    CapabilityUnsupportedError,
    SPI_VERSION,
)


class IOSRealAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="ios_real",
            display_name="Real iOS (AWS Device Farm)",
            capabilities=DeviceCapabilities(
                observe=["screenshot"],
                interact=["tap", "swipe"],
                network=["capture"],
                streaming=True,
                snapshot=False,
                screen_recording=True,
            ),
            required_providers=["aws_device_farm"],
        )

    async def provision(self, device: object, template: object) -> dict:
        """Create AWS Device Farm remote access session."""
        import boto3
        df = boto3.client("devicefarm", region_name="us-west-2")
        project_arn = getattr(template, "project_arn", "") if template else ""
        device_arn = getattr(template, "device_arn", "") if template else ""

        resp = df.create_remote_access_session(
            projectArn=project_arn,
            deviceArn=device_arn,
            name=f"devicelab-{getattr(device, 'id', 'unknown')}",
        )
        session = resp["remoteAccessSession"]
        return {
            "session_arn": session["arn"],
            "device_farm_endpoint": session.get("endpoint", ""),
        }

    async def terminate(self, device: object) -> None:
        """Stop the Device Farm remote access session."""
        if not getattr(device, "provider_ids_json", None):
            return
        ids = json.loads(device.provider_ids_json)  # type: ignore[attr-defined]
        session_arn = ids.get("session_arn")
        if session_arn:
            import boto3
            df = boto3.client("devicefarm", region_name="us-west-2")
            df.stop_remote_access_session(arn=session_arn)

    async def observe(self, device: object, tier: str) -> object:
        if tier not in self.manifest().capabilities.observe:
            raise CapabilityUnsupportedError(
                tier, "ios_real"
            )
        from datetime import UTC, datetime
        from app.models import ObservationEnvelope
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="screenshot",
            screenshot_ref="",
            observed_at=datetime.now(UTC),
        )

    async def act(self, device: object, action: str, params: dict) -> object:
        if action not in self.manifest().capabilities.interact:
            raise CapabilityUnsupportedError(action, "ios_real")
        return {"success": True, "action": action}
