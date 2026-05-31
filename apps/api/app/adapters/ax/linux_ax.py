"""
Linux AX tree extractor — copied from viralmind-ai/accessibility-tree-parsers (MIT).
Extracts the AT-SPI accessibility tree via D-Bus and returns a JSON-serializable structure.
Runs on the remote EC2 instance, invoked via SSM.
"""
import json
import subprocess
import sys


def extract_ax_tree(pid: int | None = None) -> dict:
    """Extract the AT-SPI accessibility tree for a process or the focused window."""
    try:
        import pyatspi  # type: ignore[import]
    except ImportError:
        return {"error": "pyatspi not available", "nodes": []}

    def _node_to_dict(node: object, depth: int = 0, max_depth: int = 10) -> dict:
        if depth > max_depth:
            return {}
        try:
            result: dict = {
                "role": str(node.getRoleName()),  # type: ignore[attr-defined]
                "name": str(node.name or ""),  # type: ignore[attr-defined]
                "description": str(node.description or ""),  # type: ignore[attr-defined]
                "states": [str(s) for s in node.getState().getStates()],  # type: ignore[attr-defined]
            }
            children = []
            for child in node:  # type: ignore[union-attr]
                child_dict = _node_to_dict(child, depth + 1, max_depth)
                if child_dict:
                    children.append(child_dict)
            if children:
                result["children"] = children
            return result
        except Exception:
            return {}

    try:
        desktop = pyatspi.Registry.getDesktop(0)  # type: ignore[attr-defined]
        nodes = []
        for app in desktop:
            if pid and app.get_process_id() != pid:  # type: ignore[attr-defined]
                continue
            nodes.append(_node_to_dict(app))
        return {"nodes": nodes}
    except Exception as e:
        return {"error": str(e), "nodes": []}


def extract_focused_ax_tree() -> dict:
    """Extract AX tree for the currently focused application."""
    return extract_ax_tree(pid=None)


if __name__ == "__main__":
    pid_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print(json.dumps(extract_ax_tree(pid_arg), indent=2))
