# test_runs.py — TestRun service: orchestrate recipe-backed test runs and produce JUnit XML
from __future__ import annotations
import json
import uuid
from datetime import UTC, datetime
from xml.etree import ElementTree as ET
from sqlmodel import Session
from app.models import TestRun, TestRunCreate


async def create_test_run(
    db: Session,
    workspace_id: uuid.UUID,
    body: TestRunCreate,
) -> TestRun:
    """Create TestRun record, execute recipe, populate steps_json and summary_json."""
    from app.services.recipes.runner import run_recipe

    run = TestRun(
        workspace_id=workspace_id,
        device_id=body.device_id,
        recipe_id=body.recipe_id,
        collect_artifacts=body.collect_artifacts,
        status="running",
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        recipe_run = await run_recipe(db, workspace_id, body.device_id, body.recipe_id)
        steps = json.loads(recipe_run.steps_json) if getattr(recipe_run, "steps_json", None) else []
        run.steps_json = json.dumps(steps)
        run.summary_json = json.dumps(build_summary(steps))
        run.recipe_run_id = recipe_run.id
        run.status = "complete" if recipe_run.status == "complete" else "failed"
    except Exception as exc:
        run.status = "failed"
        run.steps_json = json.dumps([])
        run.summary_json = json.dumps({"total": 0, "passed": 0, "failed": 1, "skipped": 0})

    run.completed_at = datetime.now(UTC)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_test_run(db: Session, run_id: uuid.UUID) -> TestRun | None:
    return db.get(TestRun, run_id)


def build_junit_xml(run: TestRun) -> str:
    """Produce JUnit XML string from a completed TestRun."""
    steps = json.loads(run.steps_json or "[]")
    summary = json.loads(run.summary_json or "{}")
    total = summary.get("total", len(steps))
    failed = summary.get("failed", 0)

    recipe_name = str(run.recipe_id) if run.recipe_id else "unknown"
    started = run.started_at or datetime.now(UTC)
    completed = run.completed_at or datetime.now(UTC)
    total_s = (completed - started).total_seconds()

    suite = ET.Element("testsuite", name=recipe_name, tests=str(total), failures=str(failed), time=str(total_s))
    for step in steps:
        step_id = step.get("id", "step")
        duration_ms = step.get("duration_ms", 0)
        case = ET.SubElement(suite, "testcase", name=str(step_id), time=str(duration_ms / 1000))
        if step.get("status") == "failed":
            failure = ET.SubElement(case, "failure")
            failure.set("message", step.get("error", "step failed"))
            failure.set("type", step.get("error_code", "STEP_FAILED"))

    return ET.tostring(suite, encoding="unicode", xml_declaration=False)


def build_summary(steps: list[dict]) -> dict:
    """Return {total, passed, failed, skipped} counts from steps list."""
    total = len(steps)
    failed = sum(1 for s in steps if s.get("status") == "failed")
    return {"total": total, "passed": total - failed, "failed": failed, "skipped": 0}
