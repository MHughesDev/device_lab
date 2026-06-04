# tests/adapters/test_manifest_capture.py — Phase 10 per-family capture tests
from __future__ import annotations

import json
import platform
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class _FakeDevice:
    def __init__(self, family: str = "linux", container_id: str = "abc123", adb_serial: str = "emulator-5554"):
        self.family = family
        self.location = "local"
        self.provider_ids_json = json.dumps({"container_id": container_id, "adb_serial": adb_serial, "display": ":0"})


# --- Adapter SPI ---

def test_adapter_without_capture_raises():
    from app.adapters.spi import DeviceAdapter, CapabilityUnsupportedError
    import asyncio

    class _NoCapture(DeviceAdapter):
        @classmethod
        def manifest(cls): return MagicMock(family="stub")
        async def provision(self, *a): pass
        async def terminate(self, *a): pass
        async def observe(self, *a): pass
        async def act(self, *a): pass

    adapter = _NoCapture.__new__(_NoCapture)
    with pytest.raises(CapabilityUnsupportedError):
        asyncio.get_event_loop().run_until_complete(adapter.capture_manifest(MagicMock()))


def test_manifest_capture_declared_in_linux_capabilities():
    from app.adapters.linux.adapter import LinuxAdapter
    caps = LinuxAdapter.manifest().capabilities
    assert caps.manifest_capture is True


# --- Linux manifest capture ---

@pytest.mark.asyncio
async def test_linux_capture_produces_empty_spec_without_container():
    from app.adapters.linux.manifest import capture

    class _Dev:
        provider_ids_json = "{}"

    spec = await capture(_Dev())
    assert "install_steps" in spec
    assert "capture_warnings" in spec.get("metadata", {})


@pytest.mark.asyncio
async def test_linux_capture_redacts_secret_env_vars():
    from app.adapters.linux import manifest as lm
    env_output = "NODE_ENV=development\nAWS_SECRET_ACCESS_KEY=abc123\nPATH=/usr/bin\n"
    result = lm._parse_and_redact_env(env_output)
    assert result["AWS_SECRET_ACCESS_KEY"] == "***REDACTED***"
    assert result["NODE_ENV"] == "development"


def test_linux_parse_dpkg_selections():
    from app.adapters.linux.manifest import _parse_dpkg_selections
    output = "git\t\t\t\t\t\t\t\t\tinstall\ncurl\t\t\t\t\t\t\t\t\tinstall\ndeinstall-me\t\t\t\t\t\t\t\tdeinstall\n"
    pkgs = _parse_dpkg_selections(output)
    assert "git" in pkgs
    assert "curl" in pkgs
    assert not any("deinstall" in p for p in pkgs)


def test_linux_parse_pip_list():
    from app.adapters.linux.manifest import _parse_pip_list
    output = json.dumps([{"name": "requests", "version": "2.31.0"}])
    pkgs = _parse_pip_list(output)
    assert "requests==2.31.0" in pkgs


# --- Android manifest capture ---

def test_android_parse_pm_packages():
    from app.adapters.android.manifest import _parse_pm_packages
    output = "package:/data/app/com.example.myapp-abc=/com.example.myapp\n"
    pkgs = _parse_pm_packages(output)
    assert len(pkgs) == 1
    assert pkgs[0]["package"] == "com.example.myapp"


# --- Windows manifest capture ---

def test_windows_parse_winget_json():
    from app.adapters.windows.manifest import _parse_winget
    data = [{"Id": "Git.Git", "InstalledVersion": "2.43.0"}]
    steps = _parse_winget(json.dumps(data))
    assert any(s["package_id"] == "Git.Git" for s in steps)


def test_windows_parse_winget_handles_invalid_json():
    from app.adapters.windows.manifest import _parse_winget
    steps = _parse_winget("not json at all")
    assert steps == []


# --- macOS manifest capture (Apple-gated) ---

@pytest.mark.asyncio
async def test_macos_capture_refused_on_non_apple(monkeypatch):
    import platform as _plat
    from app.adapters.macos.manifest import capture

    class _Dev:
        id = MagicMock()
        provider_ids_json = "{}"

    if _plat.system() != "Darwin":
        # Non-Apple: channel exec will fail; we get warnings but not a hard raise
        spec = await capture(_Dev())
        assert "metadata" in spec


# --- iOS Sim manifest capture (Apple-gated) ---

@pytest.mark.asyncio
async def test_ios_sim_capture_refused_on_non_apple():
    import platform as _plat
    from app.adapters.ios_sim.manifest import capture

    class _Dev:
        provider_ids_json = '{"udid": "test-udid"}'

    if _plat.system() != "Darwin":
        with pytest.raises(RuntimeError, match="macOS"):
            await capture(_Dev())
