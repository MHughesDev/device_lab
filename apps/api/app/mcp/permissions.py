from enum import IntEnum


class Role(IntEnum):
    """Permission roles — each is a superset of the previous."""
    observe = 1
    interact = 2
    test = 3
    manage = 4
    admin = 5
    dangerous = 6


ROLE_TOOLS: dict[Role, set[str]] = {
    Role.observe: {
        "workspace_status",
        "list_devices",
        "get_device",
        "list_templates",
        "cost_status",
        "screenshot",
        "get_accessibility_tree",
        # OCR / visual search — control-plane, read-only
        "ocr_screenshot",
        "find_on_screen",
        # Read-only system info
        "get_screen_size",
        "list_windows",
        "list_processes",
        "list_directory",
        # Browser read-only
        "list_tabs",
        "get_console_logs",
        "get_network_requests",
    },
    Role.interact: {
        "click",
        "double_click",
        "right_click",
        "mouse_move",
        "drag",
        "scroll",
        "cursor_position",
        "type",
        "key",
        "get_evidence",
        "start_recording",
        "stop_recording",
        "get_recording_status",
        "get_recording_artifact",
        # Extended keyboard
        "key_down",
        "key_up",
        # Clipboard
        "get_clipboard",
        "set_clipboard",
        # App / navigation
        "launch_app",
        "navigate",
        # Wait
        "wait_for",
        # Window management
        "focus_window",
        "resize_window",
        # Mobile touch gestures
        "long_press",
        "pinch",
        "press_button",
        # Browser tab / dialog management
        "new_tab",
        "close_tab",
        "switch_tab",
        "handle_dialog",
    },
    Role.test: {
        "list_recipes",
        "get_recipe",
        "upload_file",
        "download_file",
        # Shell and filesystem (potentially destructive)
        "run_shell",
        "read_file",
        "write_file",
        "kill_process",
    },
    Role.manage: {
        "create_recipe",
        "update_recipe",
        "run_recipe",
        "list_device_templates",
        "create_device",
        "stop_device",
        "start_device",
        "terminate_device",
    },
    Role.admin: {
        "list_cloud_accounts",
        "create_cloud_account",
        "run_preflight",
        "bootstrap",
        "cost_policy",
    },
    Role.dangerous: {
        "force_terminate",
        "snapshot_delete",
        "raw_shell",
    },
}


def allowed_tools(role: Role) -> set[str]:
    """Return the cumulative set of tools allowed at this role and below."""
    tools: set[str] = set()
    for r in Role:
        if r <= role:
            tools |= ROLE_TOOLS.get(r, set())
    return tools


def parse_role(name: str) -> Role:
    try:
        return Role[name.lower()]
    except KeyError:
        return Role.observe
