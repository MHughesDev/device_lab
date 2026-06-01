# test_local_provision_phase08.py — Tests for Phase 08 framebuffer fixes (08-03, 08-04, 08-05)
from __future__ import annotations
from unittest.mock import MagicMock, patch


class TestLinuxLocalProvision:
    def test_linux_local_starts_xvfb(self) -> None:
        from app.adapters.linux.local_provision import _XVFB_ENTRYPOINT
        assert "Xvfb" in _XVFB_ENTRYPOINT
        assert "DISPLAY=:0" in _XVFB_ENTRYPOINT

    def test_linux_provision_sets_display_env(self) -> None:
        import asyncio
        from unittest.mock import MagicMock, patch

        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        template = MagicMock()
        template.capability_json = None
        device = MagicMock()
        device.workspace_id = "ws-1"
        device.id = "dev-1"

        with patch("app.adapters.linux.local_provision._get_docker", return_value=mock_client):
            result = asyncio.get_event_loop().run_until_complete(
                __import__("app.adapters.linux.local_provision", fromlist=["provision"]).provision(
                    device, template
                )
            )

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs.get("environment", {}).get("DISPLAY") == ":0"
        assert result["display"] == ":0"


class TestWindowsQemuCmd:
    def test_windows_qemu_cmd_has_display_adapter(self) -> None:
        from app.adapters.windows.local_provision import _build_qemu_cmd
        cmd = _build_qemu_cmd("/path/to/image.qcow2", 15900, "test-vm", vnc_port=0)
        assert "-device" in cmd
        assert "virtio-vga" in cmd

    def test_windows_qemu_cmd_no_blind_display_none(self) -> None:
        from app.adapters.windows.local_provision import _build_qemu_cmd
        cmd = _build_qemu_cmd("/path/to/image.qcow2", 15900, "test-vm", vnc_port=0)
        # -display none is the forbidden pattern — VNC is used instead
        joined = " ".join(cmd)
        assert "-display none" not in joined
        # VNC display is present
        assert "vnc=" in joined or "vnc" in joined

    def test_windows_qemu_cmd_vnc_loopback_only(self) -> None:
        from app.adapters.windows.local_provision import _build_qemu_cmd
        cmd = _build_qemu_cmd("/path/to/image.qcow2", 15900, "test-vm", vnc_port=1)
        joined = " ".join(cmd)
        assert "127.0.0.1" in joined


class TestMacOSQemuCmd:
    def test_macos_qemu_cmd_has_display_adapter(self) -> None:
        from app.adapters.macos.local_provision import _build_qemu_cmd
        cmd = _build_qemu_cmd("/path/to/image.qcow2", 16000, "test-vm", vnc_port=0)
        assert "-device" in cmd
        assert "virtio-gpu" in cmd

    def test_macos_qemu_cmd_no_blind_display_none(self) -> None:
        from app.adapters.macos.local_provision import _build_qemu_cmd
        cmd = _build_qemu_cmd("/path/to/image.qcow2", 16000, "test-vm", vnc_port=0)
        joined = " ".join(cmd)
        assert "-display none" not in joined
        assert "vnc" in joined

    def test_macos_local_still_refused_on_non_apple(self) -> None:
        from unittest.mock import MagicMock, patch
        from app.services.local.host_probe import HostCapabilities

        non_apple_caps = HostCapabilities(
            total_ram_mb=8192, total_vcpu=4, free_disk_mb=50000,
            virtualization_available=True, os="linux", arch="x86_64", is_apple_hardware=False,
            docker_available=True,
        )

        import asyncio
        template = MagicMock()
        device = MagicMock()
        device.id = "dev-1"

        with patch("app.adapters.macos.local_provision.probe_host", return_value=non_apple_caps):
            with pytest.raises(Exception):
                asyncio.get_event_loop().run_until_complete(
                    __import__("app.adapters.macos.local_provision", fromlist=["provision"]).provision(
                        device, template
                    )
                )


import pytest
