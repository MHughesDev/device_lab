# transport/local_shell.py — LocalShellChannel: subprocess channel for host-local commands
from __future__ import annotations
import asyncio
import shutil
import subprocess

from app.transport.channel import Channel, ExecResult


class LocalShellChannel(Channel):
    """Channel that runs commands on the local host via subprocess.

    Used for ios_sim local: xcrun simctl and screencapture run directly
    on the same macOS host as the control plane, with no container or VM hop.
    """

    async def exec(self, command: str | list[str], timeout_ms: int = 30_000) -> ExecResult:
        if isinstance(command, list):
            shell_cmd = " && ".join(command)
        else:
            shell_cmd = command

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    shell_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout_ms / 1000,
                ),
            )
            return ExecResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return ExecResult(stdout="", stderr="Timeout waiting for local command", exit_code=-1)

    async def push_file(self, local_path: str, remote_path: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: shutil.copy2(local_path, remote_path))

    async def pull_file(self, remote_path: str, local_path: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: shutil.copy2(remote_path, local_path))

    async def heartbeat(self) -> bool:
        return True  # local host is always reachable
