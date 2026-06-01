# ssm.py — SSMChannel: Channel implementation over AWS Systems Manager Run Command
from __future__ import annotations
import asyncio
import base64
import time
from pathlib import Path
from typing import Sequence

import boto3

from app.transport.channel import Channel, ExecResult

_TERMINAL = {"Success", "Failed", "Cancelled", "TimedOut"}


class SSMChannel(Channel):
    """Channel implementation that wraps AWS SSM Run Command.

    One instance maps 1:1 with a single EC2 instance. The `document`
    parameter selects the SSM document used for execution:
      - "AWS-RunShellScript"    (default) for Linux, macOS, iOS Sim
      - "AWS-RunPowerShellScript" for Windows
    """

    def __init__(
        self,
        instance_id: str,
        region: str,
        document: str = "AWS-RunShellScript",
    ) -> None:
        self._instance_id = instance_id
        self._region = region
        self._document = document
        self._client = boto3.client("ssm", region_name=region)

    # ------------------------------------------------------------------
    # Channel interface
    # ------------------------------------------------------------------

    async def exec(
        self,
        command: str | Sequence[str],
        timeout_ms: int = 30_000,
    ) -> ExecResult:
        """Send one or more shell commands and wait for completion."""
        commands = [command] if isinstance(command, str) else list(command)
        resp = self._client.send_command(
            InstanceIds=[self._instance_id],
            DocumentName=self._document,
            Parameters={"commands": commands},
        )
        command_id = resp["Command"]["CommandId"]
        return self._poll(command_id, timeout_ms)

    async def push_file(self, local_path: str, remote_path: str) -> None:
        """Base64-encode a local file and decode it on the remote host."""
        data = Path(local_path).read_bytes()
        b64 = base64.b64encode(data).decode()
        if self._document == "AWS-RunPowerShellScript":
            cmd = (
                f"$b = [System.Convert]::FromBase64String('{b64}'); "
                f"[System.IO.File]::WriteAllBytes('{remote_path}', $b)"
            )
        else:
            cmd = f"echo '{b64}' | base64 -d > {remote_path}"
        await self.exec(cmd)

    async def pull_file(self, remote_path: str, local_path: str) -> None:
        """Base64-encode a remote file and decode it locally."""
        if self._document == "AWS-RunPowerShellScript":
            cmd = f"[Convert]::ToBase64String([IO.File]::ReadAllBytes('{remote_path}'))"
        else:
            cmd = f"base64 -w 0 {remote_path}"
        result = await self.exec(cmd)
        data = base64.b64decode(result.stdout.strip())
        Path(local_path).write_bytes(data)

    async def heartbeat(self) -> bool:
        """Ping the instance with a no-op command. Returns True on Success."""
        try:
            result = await self.exec("true" if self._document != "AWS-RunPowerShellScript" else "exit 0")
            return result.exit_code == 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _poll(self, command_id: str, timeout_ms: int) -> ExecResult:
        """Block (synchronously) until the SSM command reaches a terminal state."""
        deadline = time.monotonic() + timeout_ms / 1000.0
        while time.monotonic() < deadline:
            time.sleep(1)
            inv = self._client.get_command_invocation(
                CommandId=command_id,
                InstanceId=self._instance_id,
            )
            if inv["Status"] in _TERMINAL:
                return ExecResult(
                    stdout=inv.get("StandardOutputContent", ""),
                    stderr=inv.get("StandardErrorContent", ""),
                    exit_code=inv.get("ResponseCode", 0),
                )
        return ExecResult(stdout="", stderr="Timeout waiting for SSM command", exit_code=-1)
