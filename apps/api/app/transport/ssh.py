# transport/ssh.py — SSHChannel: asyncssh transport for local VMs (Windows/macOS)
from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING

from app.transport.channel import Channel, ExecResult

if TYPE_CHECKING:
    import asyncssh as _asyncssh  # type: ignore[import]


class SSHChannel(Channel):
    """Channel implementation over SSH (asyncssh) for local VMs."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "user",
        password: str | None = None,
        key_path: str | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._key_path = key_path
        self._conn: "_asyncssh.SSHClientConnection | None" = None

    async def _connect(self) -> "_asyncssh.SSHClientConnection":
        if self._conn is None:
            import asyncssh  # type: ignore[import]
            kwargs: dict = {
                "host": self._host,
                "port": self._port,
                "username": self._username,
                "known_hosts": None,  # local VMs skip host-key verification
            }
            if self._password is not None:
                kwargs["password"] = self._password
            if self._key_path is not None:
                kwargs["client_keys"] = [self._key_path]
            self._conn = await asyncssh.connect(**kwargs)
        return self._conn

    async def exec(self, command: str | list[str], timeout_ms: int = 30_000) -> ExecResult:
        if isinstance(command, list):
            shell_cmd = " && ".join(command)
        else:
            shell_cmd = command

        conn = await self._connect()
        try:
            result = await asyncio.wait_for(
                conn.run(shell_cmd, check=False),
                timeout=timeout_ms / 1000,
            )
            return ExecResult(
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                exit_code=result.exit_status if result.exit_status is not None else 0,
            )
        except asyncio.TimeoutError:
            return ExecResult(stdout="", stderr="Timeout waiting for SSH command", exit_code=-1)

    async def push_file(self, local_path: str, remote_path: str) -> None:
        conn = await self._connect()
        async with conn.start_sftp_client() as sftp:
            await sftp.put(local_path, remote_path)

    async def pull_file(self, remote_path: str, local_path: str) -> None:
        conn = await self._connect()
        async with conn.start_sftp_client() as sftp:
            await sftp.get(remote_path, local_path)

    async def heartbeat(self) -> bool:
        try:
            conn = await asyncio.wait_for(self._connect(), timeout=5)
            result = await asyncio.wait_for(conn.run("echo ok", check=False), timeout=5)
            return result.exit_status == 0
        except Exception:
            return False

    async def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
