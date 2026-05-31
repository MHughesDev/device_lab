# observation.py — Android AX observation via uiautomator2 and adb screencap
from __future__ import annotations
import json
from datetime import UTC, datetime

from app.adapters.spi import CapabilityUnsupportedError
from app.models import ObservationEnvelope

_SUPPORTED_TIERS = {"ax_tree", "screenshot"}


async def observe_android(device: object, tier: str) -> ObservationEnvelope:
    """
    tier='ax': dump UI hierarchy via uiautomator2.
    tier='screenshot': adb exec-out screencap -p → base64 PNG.
    """
    if tier not in _SUPPORTED_TIERS:
        raise CapabilityUnsupportedError(tier, "android")

    adb_serial = _get_adb_serial(device)

    if tier == "ax_tree":
        structured = _dump_ax_tree(adb_serial)
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="ax",
            structured=structured,
            observed_at=datetime.now(UTC),
        )
    else:  # screenshot
        import subprocess, base64
        result = subprocess.run(
            ["adb", "-s", adb_serial, "exec-out", "screencap", "-p"],
            capture_output=True,
        )
        screenshot_ref = base64.b64encode(result.stdout).decode()
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="screenshot",
            screenshot_ref=screenshot_ref,
            observed_at=datetime.now(UTC),
        )


def _get_adb_serial(device: object) -> str:
    """Extract adb_serial from device.provider_ids_json."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    return ids.get("adb_serial", "emulator-5554")


def _dump_ax_tree(adb_serial: str) -> dict:
    """Connect uiautomator2 and dump AX hierarchy into structured dict."""
    try:
        import uiautomator2 as u2  # type: ignore[import]
        d = u2.connect(adb_serial)
        xml = d.dump_hierarchy()
        return _parse_xml_hierarchy(xml)
    except Exception as exc:
        return {"nodes": [], "focused": None, "error": str(exc)}


def _parse_xml_hierarchy(xml: str) -> dict:
    """Parse uiautomator2 XML hierarchy into structured dict."""
    from xml.etree import ElementTree as ET
    nodes = []
    try:
        root = ET.fromstring(xml)
        for elem in root.iter():
            node = {
                "class": elem.get("class", ""),
                "resource-id": elem.get("resource-id", ""),
                "content-desc": elem.get("content-desc", ""),
                "text": elem.get("text", ""),
                "bounds": elem.get("bounds", ""),
                "clickable": elem.get("clickable", "false") == "true",
            }
            nodes.append(node)
    except Exception:
        pass
    return {"nodes": nodes, "focused": None}
