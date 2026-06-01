# transport/adb.py — ADBChannel: direct adb transport for local Android devices
from __future__ import annotations
import asyncio
import subprocess

from app.transport.channel import Channel, ExecResult


class ADBChannel(Channel):
    """Channel implementation over the adb CLI for locally-accessible Android emulators."""

    def __init__(self, serial: str) -> None:
        self._serial = serial

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
                    ["adb", "-s", self._serial, "shell", shell_cmd],
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
            return ExecResult(stdout="", stderr="Timeout waiting for adb command", exit_code=-1)

    async def push_file(self, local_path: str, remote_path: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["adb", "-s", self._serial, "push", local_path, remote_path],
                capture_output=True,
                check=True,
            ),
        )

    async def pull_file(self, remote_path: str, local_path: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["adb", "-s", self._serial, "pull", remote_path, local_path],
                capture_output=True,
                check=True,
            ),
        )

    async def heartbeat(self) -> bool:
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ["adb", "-s", self._serial, "get-state"],
                        capture_output=True,
                        text=True,
                    ),
                ),
                timeout=5,
            )
            return result.returncode == 0 and "device" in result.stdout
        except Exception:
            return False
