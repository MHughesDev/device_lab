"""
Filtered tool manifest generation.
Given a device family, device state, and client role, return only the tools
that are valid for this combination.
"""
from __future__ import annotations

from app.mcp.capabilities import DeviceCapabilities, get_capabilities
from app.mcp.permissions import Role, allowed_tools

INTERACT_STATES = {"ready"}
OBSERVE_STATES = {"ready", "stopping", "stopped"}
LIFECYCLE_STATES = {"requested", "preflight_blocked", "provisioning",
                    "bootstrapping_agent", "ready", "stopping", "stopped"}


def _capability_tools(caps: DeviceCapabilities, device_state: str) -> set[str]:
    tools: set[str] = {"workspace_status", "list_devices", "get_device", "list_templates", "cost_status"}

    if device_state in OBSERVE_STATES:
        if caps.observe.screenshot:
            tools.add("screenshot")
        if caps.observe.ax_tree:
            tools.add("get_accessibility_tree")

    if device_state in INTERACT_STATES:
        interact = caps.interact
        if interact.click:
            tools.add("click")
        if interact.double_click:
            tools.add("double_click")
        if interact.right_click:
            tools.add("right_click")
        if interact.mouse_move:
            tools.add("mouse_move")
        if interact.drag:
            tools.add("drag")
        if interact.scroll:
            tools.add("scroll")
        if interact.cursor_position:
            tools.add("cursor_position")
        if interact.type:
            tools.add("type")
        if interact.key:
            tools.add("key")
        tools.add("get_evidence")

        if caps.screen_recording.supported:
            tools |= {"start_recording", "stop_recording", "get_recording_status", "get_recording_artifact"}

    if device_state in LIFECYCLE_STATES:
        if caps.lifecycle.stop:
            tools.add("stop_device")
        if caps.lifecycle.start:
            tools.add("start_device")
        if caps.lifecycle.terminate:
            tools.add("terminate_device")

    return tools


def build_manifest(family: str, device_state: str, role: Role) -> dict:
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
            "observation_tier_max": "screenshot" if not caps.observe.vlm else "vlm",
            "dangerous_mode": role >= Role.dangerous,
        },
        "warnings": warnings,
    }
