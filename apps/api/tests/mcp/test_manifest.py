import pytest

from app.mcp.manifest import build_manifest
from app.mcp.permissions import Role


class TestBuildManifest:
    def test_linux_ready_observe_role(self) -> None:
        manifest = build_manifest("linux", "ready", Role.observe)
        tools = set(manifest["tool_groups"])
        assert "observe" in tools
        assert "workspace_status" in tools
        assert "list_devices" in tools
        # interact tools require interact role
        assert "click" not in tools

    def test_browser_ready_interact_role(self) -> None:
        manifest = build_manifest("browser", "ready", Role.interact)
        tools = set(manifest["tool_groups"])
        assert "click" in tools
        assert "type_text" in tools
        assert "fill_form" in tools
        assert "run_steps" in tools

    def test_stopped_device_no_interact_tools(self) -> None:
        manifest = build_manifest("linux", "stopped", Role.interact)
        tools = set(manifest["tool_groups"])
        assert "click" not in tools
        assert "type_text" not in tools

    def test_stopped_device_has_observe(self) -> None:
        manifest = build_manifest("linux", "stopped", Role.observe)
        tools = set(manifest["tool_groups"])
        assert "observe" in tools

    def test_observe_role_excludes_lifecycle_write(self) -> None:
        manifest = build_manifest("linux", "ready", Role.observe)
        tools = set(manifest["tool_groups"])
        assert "create_recipe" not in tools
        assert "create_cloud_account" not in tools

    def test_manage_role_includes_lifecycle(self) -> None:
        manifest = build_manifest("linux", "ready", Role.manage)
        tools = set(manifest["tool_groups"])
        assert "terminate_device" in tools
        assert "stop_device" in tools

    def test_admin_role_includes_cloud_accounts(self) -> None:
        manifest = build_manifest("linux", "ready", Role.admin)
        tools = set(manifest["tool_groups"])
        assert "list_cloud_accounts" in tools

    def test_dangerous_role_includes_raw_shell(self) -> None:
        manifest = build_manifest("linux", "ready", Role.dangerous)
        tools = set(manifest["tool_groups"])
        assert "raw_shell" in tools

    def test_stopped_device_warns_about_interaction(self) -> None:
        manifest = build_manifest("linux", "stopped", Role.interact)
        assert any("interaction" in w or "ready" in w for w in manifest["warnings"])

    def test_browser_family_excludes_files_capability(self) -> None:
        # browser family doesn't have files.upload in phase 03
        manifest = build_manifest("browser", "ready", Role.test)
        # browser doesn't have files capability so upload not enabled
        caps = manifest["capabilities"]
        assert caps["files"]["upload"] is False

    def test_linux_family_has_files_capability(self) -> None:
        manifest = build_manifest("linux", "ready", Role.test)
        caps = manifest["capabilities"]
        assert caps["files"]["upload"] is True
