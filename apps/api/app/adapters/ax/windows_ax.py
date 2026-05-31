"""
Windows AX tree extractor — copied from viralmind-ai/accessibility-tree-parsers (MIT).
Uses UI Automation (UIA) via pywinauto or comtypes to extract the accessibility tree.
"""
import json
import sys


def extract_ax_tree(process_name: str | None = None) -> dict:
    """Extract UIA accessibility tree for the focused or named process."""
    try:
        from pywinauto import Desktop  # type: ignore[import]
        return _pywinauto_extract(process_name)
    except ImportError:
        pass
    try:
        return _uia_comtypes_extract(process_name)
    except Exception as e:
        return {"error": str(e), "nodes": []}


def _pywinauto_extract(process_name: str | None) -> dict:
    from pywinauto import Desktop  # type: ignore[import]

    def _ctrl_to_dict(ctrl: object, depth: int = 0, max_depth: int = 8) -> dict:
        if depth > max_depth:
            return {}
        try:
            info = ctrl.element_info  # type: ignore[attr-defined]
            node: dict = {
                "role": str(info.control_type),
                "name": str(info.name or ""),
                "class": str(info.class_name or ""),
            }
            children = [_ctrl_to_dict(c, depth + 1, max_depth) for c in ctrl.children()]  # type: ignore[attr-defined]
            children = [c for c in children if c]
            if children:
                node["children"] = children
            return node
        except Exception:
            return {}

    try:
        desktop = Desktop(backend="uia")
        if process_name:
            windows = desktop.windows(title_re=f".*{process_name}.*")
        else:
            windows = [desktop.active()]
        return {"nodes": [_ctrl_to_dict(w) for w in windows if w]}
    except Exception as e:
        return {"error": str(e), "nodes": []}


def _uia_comtypes_extract(process_name: str | None) -> dict:
    """Fallback: use comtypes + UIAutomation directly."""
    import comtypes.client  # type: ignore[import]
    UIAuto = comtypes.client.CreateObject("{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=comtypes.client.IUnknown)  # type: ignore
    return {"error": "comtypes UIA fallback not fully implemented", "nodes": []}


if __name__ == "__main__":
    proc = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(extract_ax_tree(proc), indent=2))
