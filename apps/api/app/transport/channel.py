# channel.py — Channel SPI: transport abstraction between adapters and remote devices
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int


class Channel(ABC):
    """Transport-agnostic command channel between the control plane and a device."""

    @abstractmethod
    async def exec(self, command: str | list[str], timeout_ms: int = 30_000) -> ExecResult:
        """Run a command (or ordered list of commands) and return stdout/stderr/exit_code."""
        ...

    @abstractmethod
    async def push_file(self, local_path: str, remote_path: str) -> None:
        """Copy a local file to the remote device."""
        ...

    @abstractmethod
    async def pull_file(self, remote_path: str, local_path: str) -> None:
        """Copy a file from the remote device to local disk."""
        ...

    @abstractmethod
    async def heartbeat(self) -> bool:
        """Return True if the remote device is reachable."""
        ...

    async def close(self) -> None:
        """Release any held resources. Default is a no-op."""


class ChannelFactory:
    """Resolve a Device instance to a concrete Channel.

    Dispatches on (device.family, device.location). Unimplemented local
    families raise NotImplementedError — they will be wired in later tasks.
    """

    _SHELL_FAMILIES = {"linux", "macos", "ios_sim"}
    _PS_FAMILIES = {"windows"}

    @staticmethod
    def get(device: object) -> "Channel":
        from app.transport.ssm import SSMChannel  # late import avoids circular deps

        import json
        location: str = getattr(device, "location", "cloud")
        family: str = getattr(device, "family", "")
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")

        if location == "cloud":
            instance_id = ids.get("instance_id", "")
            region = ids.get("region", "us-east-1")
            if family in ChannelFactory._PS_FAMILIES:
                return SSMChannel(instance_id, region, document="AWS-RunPowerShellScript")
            return SSMChannel(instance_id, region)

        # local path — filled in per-family during Phase 07 task batches D–G
        if location == "local":
            if family == "linux":
                from app.transport.docker_exec import DockerExecChannel
                container_id = ids.get("container_id", "")
                return DockerExecChannel(container_id)
            if family == "android":
                raise NotImplementedError(
                    "ADBChannel not yet implemented (task 07-11)"
                )
            if family == "windows":
                raise NotImplementedError(
                    "SSHChannel not yet implemented (task 07-12)"
                )
            if family in ("macos", "ios_sim"):
                raise NotImplementedError(
                    f"Local {family} channel not yet implemented (task 07-13)"
                )

        raise ValueError(f"No channel implementation for family={family!r} location={location!r}")
