"""
macOS AX tree extractor — copied from viralmind-ai/accessibility-tree-parsers (MIT).
Uses AXUIElement API via pyobjc or AppleScript to extract the accessibility tree.
"""
import json
import sys


def extract_ax_tree(app_name: str | None = None) -> dict:
    """Extract the AXUIElement accessibility tree for the focused or named app."""
    try:
        import AppKit  # type: ignore[import]
        import ApplicationServices  # type: ignore[import]
    except ImportError:
        return _applescript_fallback(app_name)

    def _element_to_dict(element: object, depth: int = 0, max_depth: int = 8) -> dict:
        if depth > max_depth:
            return {}
        try:
            role = element.AXRole  # type: ignore[attr-defined]
            title = getattr(element, "AXTitle", "") or ""
            value = getattr(element, "AXValue", "") or ""
            children_raw = getattr(element, "AXChildren", []) or []
            node: dict = {"role": str(role), "title": str(title)}
            if value:
                node["value"] = str(value)
            children = [_element_to_dict(c, depth + 1, max_depth) for c in children_raw]
            children = [c for c in children if c]
            if children:
                node["children"] = children
            return node
        except Exception:
            return {}

    try:
        workspace = AppKit.NSWorkspace.sharedWorkspace()  # type: ignore[attr-defined]
        if app_name:
            apps = [a for a in workspace.runningApplications() if a.localizedName() == app_name]
        else:
            apps = [workspace.frontmostApplication()]
        if not apps or not apps[0]:
            return {"nodes": []}
        pid = apps[0].processIdentifier()
        app_element = ApplicationServices.AXUIElementCreateApplication(pid)  # type: ignore[attr-defined]
        return {"nodes": [_element_to_dict(app_element)]}
    except Exception as e:
        return {"error": str(e), "nodes": []}


def _applescript_fallback(app_name: str | None) -> dict:
    import subprocess
    script = f'tell application "{app_name or "System Events"}" to get entire contents of window 1'
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        return {"raw": result.stdout, "nodes": []}
    except Exception as e:
        return {"error": str(e), "nodes": []}


if __name__ == "__main__":
    app = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(extract_ax_tree(app), indent=2))
