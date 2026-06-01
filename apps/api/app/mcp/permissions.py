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
    },
    Role.test: {
        "list_recipes",
        "get_recipe",
        "upload_file",
        "download_file",
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
