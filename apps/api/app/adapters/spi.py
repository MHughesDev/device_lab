# spi.py — DeviceAdapter SPI: abstract base, manifest, and capability contracts
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

SPI_VERSION = "1.0"
SUPPORTED_SPI_VERSIONS = {"1.0"}


@dataclass
class DeviceCapabilities:
    observe: list[str] = field(default_factory=list)
    interact: list[str] = field(default_factory=list)
    network: list[str] = field(default_factory=list)
    streaming: bool = False
    snapshot: bool = False
    screen_recording: bool = False
    manifest_capture: bool = False   # Phase 10: capture_manifest() supported
    dangerous_actions: list[str] = field(default_factory=list)


@dataclass
class AdapterManifest:
    spi_version: str
    adapter_version: str
    family: str
    display_name: str
    capabilities: DeviceCapabilities
    required_providers: list[str]
    supported_regions: list[str] | None = None


class CapabilityUnsupportedError(Exception):
    """Raised when an optional adapter method is called but not supported."""
    def __init__(self, capability: str, family: str):
        self.capability = capability
        self.family = family
        super().__init__(
            f"CAPABILITY_UNSUPPORTED: '{capability}' is not available for family '{family}'"
        )


class IncompatibleAdapterError(Exception):
    """Raised when an adapter declares an unsupported SPI version."""


class DeviceAdapter(ABC):
    """
    Abstract base for all device family adapters.

    Required methods must be implemented by every adapter.
    Optional methods raise CapabilityUnsupportedError by default.
    """

    @classmethod
    @abstractmethod
    def manifest(cls) -> AdapterManifest: ...

    @abstractmethod
    async def provision(self, device: object, template: object) -> dict:
        """Provision cloud resources. Returns provider_ids dict.
        Must tag all resources with DeviceLab:Workspace and DeviceLab:Device."""
        ...

    @abstractmethod
    async def terminate(self, device: object) -> None:
        """Terminate all provider resources. Must be idempotent."""
        ...

    @abstractmethod
    async def observe(self, device: object, tier: str) -> object:
        """Return an ObservationEnvelope. Raise CapabilityUnsupportedError for unlisted tiers."""
        ...

    @abstractmethod
    async def act(self, device: object, action: str, params: dict) -> object:
        """Execute a semantic action. Raise CapabilityUnsupportedError for unlisted actions."""
        ...

    # --- Optional methods ---

    async def snapshot(self, device: object) -> object:
        raise CapabilityUnsupportedError("snapshot", self.manifest().family)

    async def stream_offer(self, device: object) -> str:
        """Return SDP offer string for WebRTC stream negotiation."""
        raise CapabilityUnsupportedError("streaming", self.manifest().family)

    async def start_recording(self, device: object, recording_id: str) -> str:
        """Start screen recording. Returns an opaque handle (PID, path, etc.)."""
        raise CapabilityUnsupportedError("screen_recording", self.manifest().family)

    async def stop_recording(self, device: object, session: object) -> str:
        """Stop recording and return the storage path."""
        raise CapabilityUnsupportedError("screen_recording", self.manifest().family)

    async def capture_artifacts(self, device: object, run_id: str) -> list[object]:
        return []

    async def cleanup_orphans(self, provider_ids: list[str], region: str) -> None:
        pass

    async def capture_manifest(self, device: object) -> dict:
        """Introspect the running device and return a spec_json payload dict.

        Implementors should return a dict conforming to the manifest spec format
        (see docs/design/manifest-spec.json). The caller creates the DeviceManifest
        row via ManifestRegistry after receiving this dict.

        Default: raises CapabilityUnsupportedError. Set capabilities.manifest_capture=True
        in the adapter's AdapterManifest when overriding.
        """
        raise CapabilityUnsupportedError("capture_manifest", self.manifest().family)
