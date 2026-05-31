import uuid
from datetime import UTC, datetime
from xml.etree import ElementTree as ET

import pytest

from app.models import TestRun
from app.services.test_runs import build_junit_xml, build_summary


def _make_run(steps=None, summary=None):
    import json
    run = TestRun(
        workspace_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        recipe_id=uuid.uuid4(),
        status="complete",
        steps_json=json.dumps(steps or []),
        summary_json=json.dumps(summary or {}),
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    return run


def test_build_summary_all_pass():
    steps = [{"id": f"s{i}", "status": "passed"} for i in range(3)]
    result = build_summary(steps)
    assert result["passed"] == 3
    assert result["failed"] == 0


def test_build_summary_one_fail():
    steps = [
        {"id": "s1", "status": "passed"},
        {"id": "s2", "status": "failed"},
        {"id": "s3", "status": "passed"},
    ]
    result = build_summary(steps)
    assert result["failed"] == 1
    assert result["passed"] == 2


def test_build_junit_xml_parseable():
    run = _make_run(steps=[{"id": "step1", "status": "passed", "duration_ms": 100}])
    xml_str = build_junit_xml(run)
    root = ET.fromstring(xml_str)
    assert root.tag == "testsuite"


def test_build_junit_xml_failure_element():
    run = _make_run(steps=[{"id": "step1", "status": "failed", "error": "oops", "duration_ms": 50}])
    xml_str = build_junit_xml(run)
    root = ET.fromstring(xml_str)
    case = root.find("testcase")
    assert case is not None
    failure = case.find("failure")
    assert failure is not None


def test_build_junit_xml_no_failure_on_pass():
    run = _make_run(steps=[{"id": "step1", "status": "passed", "duration_ms": 100}])
    xml_str = build_junit_xml(run)
    root = ET.fromstring(xml_str)
    case = root.find("testcase")
    assert case is not None
    assert case.find("failure") is None
