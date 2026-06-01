# adapters/linux/manifest.py — Linux manifest capture (Phase 10, task 10-05)
"""
Introspects a running Linux container and produces a DeviceManifest spec_json.

Parallel exec via DockerExecChannel:
  - apt packages:   dpkg --get-selections | grep install
  - pip packages:   pip3 list --format=json   (if python3 present)
  - npm globals:    npm list -g --json --depth=0  (if npm present)
  - env vars:       printenv  (secrets redacted)
  - systemd units:  systemctl list-units --state=enabled --type=service --no-pager

Ephemeral state (running processes, open files) is intentionally excluded.
Only durable installation facts are captured.
"""
from __future__ import annotations

import asyncio
import json
import logging

log = logging.getLogger(__name__)

_REDACT_PATTERNS = (
    "KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL", "PASS", "PWD", "AUTH"
)


async def capture(device: object) -> dict:
    """Introspect the running Linux container and return a spec dict."""
    import json as _json
    ids: dict = _json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    container_id: str = ids.get("container_id", "")
    display: str = ids.get("display", ":0")

    if not container_id:
        log.warning("Linux manifest capture: no container_id — returning empty spec")
        return _empty_spec()

    results = await asyncio.gather(
        _docker_exec(container_id, ["dpkg", "--get-selections"]),
        _docker_exec(container_id, ["pip3", "list", "--format=json"]),
        _docker_exec(container_id, ["npm", "list", "-g", "--json", "--depth=0"]),
        _docker_exec(container_id, ["printenv"]),
        _docker_exec(container_id, ["systemctl", "list-units", "--state=enabled", "--type=service", "--no-pager"]),
        return_exceptions=True,
    )

    apt_out, pip_out, npm_out, env_out, svc_out = results

    install_steps = []
    capture_warnings = []

    # apt packages
    if isinstance(apt_out, str):
        pkgs = _parse_dpkg_selections(apt_out)
        if pkgs:
            install_steps.append({"type": "apt", "packages": pkgs})
    else:
        capture_warnings.append(f"apt capture failed: {apt_out}")

    # pip packages
    if isinstance(pip_out, str):
        pkgs = _parse_pip_list(pip_out)
        if pkgs:
            install_steps.append({"type": "pip", "packages": pkgs})
    elif pip_out is not None:
        capture_warnings.append("pip3 not available or failed")

    # npm global packages
    if isinstance(npm_out, str):
        pkgs = _parse_npm_global(npm_out)
        if pkgs:
            install_steps.append({"type": "npm_global", "packages": pkgs})
    elif npm_out is not None:
        capture_warnings.append("npm not available or failed")

    # env vars (redacted)
    env_vars: dict[str, str] = {}
    if isinstance(env_out, str):
        env_vars = _parse_and_redact_env(env_out)

    # startup services (as shell commands)
    if isinstance(svc_out, str):
        services = _parse_enabled_services(svc_out)
        for svc in services:
            install_steps.append({"type": "shell", "command": f"systemctl enable {svc}"})

    spec = {
        "install_steps": install_steps,
        "env_vars": env_vars,
        "startup_commands": [],
        "metadata": {
            "capture_source": "linux",
            "container_id": container_id,
        },
    }
    if capture_warnings:
        spec["metadata"]["capture_warnings"] = capture_warnings
    return spec


async def _docker_exec(container_id: str, cmd: list[str]):
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        return stdout.decode("utf-8", errors="replace")
    except Exception as exc:
        return exc


def _parse_dpkg_selections(output: str) -> list[str]:
    pkgs = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == "install":
            pkg = parts[0].split(":")[0]  # strip architecture suffix
            pkgs.append(pkg)
    return pkgs[:500]  # cap at 500 packages


def _parse_pip_list(output: str) -> list[str]:
    try:
        items = json.loads(output)
        return [f"{item['name']}=={item['version']}" for item in items if isinstance(item, dict)]
    except Exception:
        return []


def _parse_npm_global(output: str) -> list[str]:
    try:
        data = json.loads(output)
        deps = data.get("dependencies", {})
        return [f"{name}@{info.get('version', 'latest')}" for name, info in deps.items()]
    except Exception:
        return []


def _parse_and_redact_env(output: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        # Redact env vars whose names suggest secrets
        if any(p in key.upper() for p in _REDACT_PATTERNS):
            env[key] = "***REDACTED***"
        else:
            env[key] = value
    return env


def _parse_enabled_services(output: str) -> list[str]:
    services = []
    for line in output.splitlines():
        parts = line.split()
        if parts and parts[0].endswith(".service"):
            svc = parts[0].removesuffix(".service")
            if not svc.startswith("getty@") and not svc.startswith("dbus"):
                services.append(svc)
    return services


def _empty_spec() -> dict:
    return {
        "install_steps": [],
        "env_vars": {},
        "startup_commands": [],
        "metadata": {"capture_warnings": ["No container_id — empty spec"]},
    }
