from enum import IntEnum


class Role(IntEnum):
    """Permission roles — each is a superset of the previous."""
    observe = 1
    interact = 2
    test = 3
    manage = 4
    admin = 5
    dangerous = 6


# Tools allowed at each role level (cumulative)
ROLE_TOOLS: dict[Role, set[str]] = {
    Role.observe: {
        "workspace_status",
        "list_devices",
        "get_device",
        "list_templates",
        "cost_status",
        "observe",
    },
    Role.interact: {
        "click",
        "type_text",
        "fill_form",
        "select_option",
        "scroll",
        "wait_for",
        "read_content",
        "run_steps",
        "get_evidence",
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
