"""
Filtered tool manifest generation.
Given a device family, device state, and client role, return only the tools
that are valid for this combination.
"""
from __future__ import annotations

from app.mcp.capabilities import DeviceCapabilities, get_capabilities
from app.mcp.permissions import Role, allowed_tools

# States in which interaction tools are valid
INTERACT_STATES = {"ready"}
# States in which observe tools are valid
OBSERVE_STATES = {"ready", "stopping", "stopped"}
# States in which lifecycle tools are valid
LIFECYCLE_STATES = {"requested", "preflight_blocked", "provisioning",
                    "bootstrapping_agent", "ready", "stopping", "stopped"}


def _capability_tools(caps: DeviceCapabilities, device_state: str) -> set[str]:
    """Tools derivable purely from device capabilities and state."""
    tools: set[str] = {"workspace_status", "list_devices", "get_device", "list_templates", "cost_status"}

    if device_state in OBSERVE_STATES:
        if caps.observe.ax_tree:
            tools.add("observe")
        if caps.observe.screenshot:
            tools.add("observe")

    if device_state in INTERACT_STATES:
        if caps.interact.click:
            tools.add("click")
        if caps.interact.type_text:
            tools.add("type_text")
        if caps.interact.fill_form:
            tools.add("fill_form")
        if caps.interact.select:
            tools.add("select_option")
        if caps.interact.scroll:
            tools.add("scroll")
        if caps.interact.key:
            tools.add("wait_for")
        tools.add("run_steps")
        tools.add("read_content")
        tools.add("get_evidence")

    if device_state in LIFECYCLE_STATES:
        if caps.lifecycle.stop:
            tools.add("stop_device")
        if caps.lifecycle.start:
            tools.add("start_device")
        if caps.lifecycle.terminate:
            tools.add("terminate_device")

    return tools


def build_manifest(
    family: str,
    device_state: str,
    role: Role,
) -> dict:
    caps = get_capabilities(family)
    cap_tools = _capability_tools(caps, device_state)
    role_tools = allowed_tools(role)
    visible = cap_tools & role_tools

    warnings = []
    if device_state not in INTERACT_STATES and role >= Role.interact:
        warnings.append(f"Device is '{device_state}' — interaction tools unavailable until state is 'ready'")

    return {
        "tool_groups": sorted(visible),
        "family": family,
        "device_state": device_state,
        "role": role.name,
        "capabilities": caps.model_dump(),
        "limits": {
            "max_steps_per_batch": 50,
            "observation_tier_max": "screenshot" if not caps.observe.vlm else "vlm",
            "dangerous_mode": role >= Role.dangerous,
        },
        "warnings": warnings,
    }
