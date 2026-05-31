# interaction.py — Android interaction via uiautomator2 (click, swipe, type, key, scroll)
from __future__ import annotations
from app.adapters.spi import CapabilityUnsupportedError

SUPPORTED_ACTIONS = {"click", "swipe", "type", "key", "scroll"}


async def act_android(device: object, action: str, params: dict) -> dict:
    """Dispatch action to uiautomator2. Raises CapabilityUnsupportedError for unsupported actions."""
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "android")

    import uiautomator2 as u2  # type: ignore[import]
    from app.adapters.android.observation import _get_adb_serial
    adb_serial = _get_adb_serial(device)
    d = u2.connect(adb_serial)

    if action == "click":
        target = params.get("target")
        if target:
            _resolve_element(d, target).click()
        else:
            d.click(params.get("x", 0), params.get("y", 0))

    elif action == "swipe":
        d.swipe(
            params.get("start_x", 0),
            params.get("start_y", 0),
            params.get("end_x", 0),
            params.get("end_y", 0),
            steps=params.get("steps", 10),
        )

    elif action == "type":
        text = params.get("text", "")
        target = params.get("target")
        if target:
            _resolve_element(d, target).set_text(text)
        else:
            d(focused=True).set_text(text)

    elif action == "key":
        keycode = params.get("keycode", "enter")
        d.press(keycode)

    elif action == "scroll":
        d(scrollable=True).scroll(steps=params.get("steps", 10))

    return {"success": True, "action": action}


def _resolve_element(d: object, target: str) -> object:
    """Resolve target string to uiautomator2 selector.
    Priority: resource-id → content-desc → text → xpath."""
    import uiautomator2 as u2  # type: ignore[import]
    if d(resourceId=target).exists:
        return d(resourceId=target)
    if d(description=target).exists:
        return d(description=target)
    if d(text=target).exists:
        return d(text=target)
    return d.xpath(target)
