# docker_exec.py — DockerExecChannel: Channel implementation over Docker exec
from __future__ import annotations
import io
import tarfile
import tempfile
from pathlib import Path

from app.transport.channel import Channel, ExecResult


class DockerExecChannel(Channel):
    """Channel implementation backed by a running Docker container.

    Uses the Docker SDK's container.exec_run for command execution,
    put_archive / get_archive for file transfer, and container.status
    for heartbeat.
    """

    def __init__(self, container_id: str, device_id: str | None = None) -> None:
        import docker
        self._client = docker.from_env()
        self._container_id = container_id
        self._container = self._client.containers.get(container_id)
        self._device_id = device_id

    # ------------------------------------------------------------------
    # Channel interface
    # ------------------------------------------------------------------

    async def exec(
        self,
        command: str | list[str],
        timeout_ms: int = 30_000,
    ) -> ExecResult:
        """Run a command inside the container and return stdout/stderr/exit_code."""
        if isinstance(command, list):
            # Join multiple commands as a shell script
            script = " && ".join(command)
            cmd_str = ["sh", "-c", script]
        else:
            cmd_str = ["sh", "-c", command]

        result = self._container.exec_run(
            cmd=cmd_str,
            demux=True,
            tty=False,
        )
        exit_code = result.exit_code or 0
        stdout_bytes, stderr_bytes = result.output or (b"", b"")
        stdout = (stdout_bytes or b"").decode(errors="replace")
        stderr = (stderr_bytes or b"").decode(errors="replace")

        if self._device_id:
            self._emit_transport(cmd_str[2] if len(cmd_str) > 2 else str(cmd_str), exit_code)

        return ExecResult(stdout=stdout, stderr=stderr, exit_code=exit_code)

    def _emit_transport(self, command_summary: str, exit_code: int) -> None:
        try:
            from app.services.device_log_bus import get_log_bus
            get_log_bus().emit(
                self._device_id,
                level="debug" if exit_code == 0 else "warn",
                source="transport",
                message=f"exec exit_code={exit_code}",
                fields={"cmd": command_summary[:200], "exit_code": exit_code},
            )
        except Exception:
            pass

    async def push_file(self, local_path: str, remote_path: str) -> None:
        """Copy a local file into the container via put_archive."""
        data = Path(local_path).read_bytes()
        remote = Path(remote_path)

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            info = tarfile.TarInfo(name=remote.name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        buf.seek(0)

        self._container.put_archive(str(remote.parent), buf)

    async def pull_file(self, remote_path: str, local_path: str) -> None:
        """Copy a file from the container to local disk via get_archive."""
        stream, _ = self._container.get_archive(remote_path)

        buf = io.BytesIO()
        for chunk in stream:
            buf.write(chunk)
        buf.seek(0)

        with tarfile.open(fileobj=buf, mode="r") as tar:
            members = tar.getmembers()
            if not members:
                raise FileNotFoundError(f"No file found at {remote_path} in container")
            member = members[0]
            extracted = tar.extractfile(member)
            if extracted is None:
                raise FileNotFoundError(f"Cannot extract {remote_path} from container")
            Path(local_path).write_bytes(extracted.read())

    async def heartbeat(self) -> bool:
        """Return True if the container is running."""
        try:
            self._container.reload()
            return self._container.status == "running"
        except Exception:
            return False

    async def close(self) -> None:
        """No persistent resources to release for Docker exec."""
