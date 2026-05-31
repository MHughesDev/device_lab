"""
Recipe runner — executes RecipeSchema steps against a device using the interaction service.
Uses pypyr as the step execution backbone with DeviceLab-specific step modules.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session

from app.models import Recipe, RecipeRun
from app.services.interaction import execute_action
from app.services.recipes.schema import RecipeSchema
from app.services.recipes.validator import parse_and_validate


TEMPLATE_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def _resolve_template(value: Any, context: dict[str, Any]) -> Any:
    """Recursively resolve {{ template }} references in strings."""
    if isinstance(value, str):
        def replacer(m: re.Match[str]) -> str:
            key = m.group(1)
            parts = key.split(".")
            v: Any = context
            for part in parts:
                if isinstance(v, dict):
                    v = v.get(part, m.group(0))
                else:
                    return m.group(0)
            return str(v)
        return TEMPLATE_RE.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_template(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_template(v, context) for v in value]
    return value


async def run_recipe(
    db: Session,
    recipe_id: uuid.UUID,
    device_id: uuid.UUID,
    inputs: dict[str, Any],
    workspace_id: uuid.UUID,
    resume_run_id: uuid.UUID | None = None,
) -> RecipeRun:
    """Execute a recipe against a device. Returns the completed RecipeRun."""
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise ValueError(f"Recipe {recipe_id} not found")

    schema = parse_and_validate(recipe.yaml_content)

    # Resolve secret_ref inputs
    resolved_inputs: dict[str, Any] = {}
    for input_name, inp_schema in schema.inputs.items():
        raw_value = inputs.get(input_name, inp_schema.default)
        if inp_schema.type == "secret_ref" and inp_schema.ref:
            from app.services.identity.broker import resolve
            raw_value = resolve(db, workspace_id, inp_schema.ref)
        resolved_inputs[input_name] = raw_value

    context: dict[str, Any] = {"inputs": resolved_inputs}

    # Find or create RecipeRun
    if resume_run_id:
        run = db.get(RecipeRun, resume_run_id)
        if not run:
            raise ValueError(f"RecipeRun {resume_run_id} not found")
        existing_steps: list[dict] = json.loads(run.steps_json or "[]")
        start_index = run.current_step_index
    else:
        run = RecipeRun(
            recipe_id=recipe_id,
            device_id=device_id,
            status="running",
            started_at=datetime.now(UTC),
            steps_json="[]",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        existing_steps = []
        start_index = 0

    run.status = "running"
    steps_log: list[dict] = list(existing_steps)

    for i, step in enumerate(schema.steps):
        if i < start_index:
            continue

        resolved_params = _resolve_template(step.params, context)

        step_record: dict[str, Any] = {
            "step_id": step.id,
            "action": step.action,
            "status": "running",
            "started_at": datetime.now(UTC).isoformat(),
        }
        steps_log.append(step_record)
        run.current_step_index = i
        run.steps_json = json.dumps(steps_log)
        db.add(run)
        db.commit()

        result = await execute_action(
            db=db,
            device_id=device_id,
            action=step.action,
            params=resolved_params,
            session_id=f"recipe:{run.id}",
        )

        step_record["status"] = "complete" if result.success else "failed"
        step_record["completed_at"] = datetime.now(UTC).isoformat()
        step_record["evidence_id"] = result.evidence_id
        if result.error:
            step_record["error"] = result.error

        if result.success:
            context["last_result"] = result.model_dump()
        else:
            steps_log[-1] = step_record
            run.steps_json = json.dumps(steps_log)
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            db.add(run)
            db.commit()
            return run

        steps_log[-1] = step_record

    run.steps_json = json.dumps(steps_log)
    run.status = "complete"
    run.completed_at = datetime.now(UTC)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
