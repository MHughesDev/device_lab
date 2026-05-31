"""
Recipe recorder — transforms a sequence of ActionResult envelopes into a recipe YAML draft.
"""
from __future__ import annotations

import yaml

from app.models import Evidence


COORDINATE_PATTERN_HINT = "# WARNING: unstable selector — use accessible name or role instead"


def _params_are_coordinate_only(params: dict) -> bool:
    """Heuristic: if target looks like 'x,y' coords it's fragile."""
    target = str(params.get("target", ""))
    return bool(target and target.replace(",", "").replace(".", "").replace(" ", "").isdigit())


def build_recipe_draft(evidence_list: list[Evidence], recipe_name: str = "recorded-recipe") -> str:
    """Turn a list of Evidence records into a recipe YAML draft string."""
    steps = []
    for i, ev in enumerate(evidence_list):
        import json
        payload: dict = json.loads(ev.request_payload_json or "{}")
        action = ev.mcp_tool
        params = {k: v for k, v in payload.items() if k != "action"}

        step: dict = {
            "id": f"step_{i + 1}",
            "action": action,
            "params": params,
        }

        if _params_are_coordinate_only(params):
            step["description"] = COORDINATE_PATTERN_HINT.lstrip("# ")

        steps.append(step)

    recipe: dict = {
        "name": recipe_name,
        "version": 1,
        "families": [],
        "inputs": {},
        "steps": steps,
        "artifacts": [{"capture_screenshot": "on_failure"}],
        "cleanup": [],
    }

    return yaml.dump(recipe, default_flow_style=False, sort_keys=False, allow_unicode=True)
