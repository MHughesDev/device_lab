"""Tests for recipe runner, validator, template resolution, and recorder."""
from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest
import yaml


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

def test_parse_and_validate_valid():
    """Parse a valid minimal recipe YAML — expect no error."""
    from app.services.recipes.validator import parse_and_validate

    recipe_yaml = """
name: test-recipe
version: 1
families: []
steps:
  - id: step_1
    action: click
    params:
      target: "#submit"
"""
    schema = parse_and_validate(recipe_yaml)
    assert schema.name == "test-recipe"
    assert len(schema.steps) == 1
    assert schema.steps[0].id == "step_1"


def test_parse_and_validate_invalid_yaml():
    """Pass invalid YAML — expect RecipeValidationError."""
    from app.services.recipes.validator import parse_and_validate, RecipeValidationError

    with pytest.raises(RecipeValidationError) as exc_info:
        parse_and_validate("not: valid: yaml: {{{")
    assert exc_info.value.errors


def test_parse_and_validate_dangerous_undeclared():
    """Step with action=raw_shell but dangerous=False should raise error."""
    from app.services.recipes.validator import parse_and_validate, RecipeValidationError

    recipe_yaml = """
name: dangerous-recipe
version: 1
steps:
  - id: step_1
    action: raw_shell
    params:
      cmd: "ls -la"
    dangerous: false
"""
    with pytest.raises(RecipeValidationError) as exc_info:
        parse_and_validate(recipe_yaml)
    assert any("dangerous" in err for err in exc_info.value.errors)


def test_parse_and_validate_family_mismatch():
    """Recipe families=[android] but device_family=browser should raise error."""
    from app.services.recipes.validator import parse_and_validate, RecipeValidationError

    recipe_yaml = """
name: android-only
version: 1
families:
  - android
steps:
  - id: step_1
    action: click
    params:
      target: "#button"
"""
    with pytest.raises(RecipeValidationError) as exc_info:
        parse_and_validate(recipe_yaml, device_family="browser")
    assert any("browser" in err for err in exc_info.value.errors)


# ---------------------------------------------------------------------------
# Template resolution tests
# ---------------------------------------------------------------------------

def test_resolve_template():
    """_resolve_template substitutes {{ inputs.base_url }} correctly."""
    from app.services.recipes.runner import _resolve_template

    context = {"inputs": {"base_url": "https://example.com"}}
    value = {"url": "{{ inputs.base_url }}/path"}
    resolved = _resolve_template(value, context)
    assert resolved == {"url": "https://example.com/path"}


def test_resolve_template_nested():
    """_resolve_template handles nested dict and list values."""
    from app.services.recipes.runner import _resolve_template

    context = {"inputs": {"user": "alice"}}
    value = [{"greeting": "Hello {{ inputs.user }}!"}]
    resolved = _resolve_template(value, context)
    assert resolved == [{"greeting": "Hello alice!"}]


# ---------------------------------------------------------------------------
# Recorder tests
# ---------------------------------------------------------------------------

def test_build_recipe_draft():
    """build_recipe_draft with two mock Evidence objects produces valid YAML with step_1 and step_2."""
    from app.services.recipes.recorder import build_recipe_draft

    ev1 = MagicMock()
    ev1.mcp_tool = "click"
    ev1.request_payload_json = json.dumps({"action": "click", "target": "#submit"})

    ev2 = MagicMock()
    ev2.mcp_tool = "type_text"
    ev2.request_payload_json = json.dumps({"action": "type_text", "target": "#input", "text": "hello"})

    draft_yaml = build_recipe_draft([ev1, ev2], recipe_name="my-test-recipe")

    # Must be parseable YAML
    parsed = yaml.safe_load(draft_yaml)
    assert parsed is not None
    assert parsed["name"] == "my-test-recipe"

    step_ids = [s["id"] for s in parsed["steps"]]
    assert "step_1" in step_ids
    assert "step_2" in step_ids

    # Check actions are preserved
    steps_by_id = {s["id"]: s for s in parsed["steps"]}
    assert steps_by_id["step_1"]["action"] == "click"
    assert steps_by_id["step_2"]["action"] == "type_text"


def test_build_recipe_draft_coordinate_hint():
    """build_recipe_draft adds a warning description for coordinate-only targets."""
    from app.services.recipes.recorder import build_recipe_draft, COORDINATE_PATTERN_HINT

    ev = MagicMock()
    ev.mcp_tool = "click"
    ev.request_payload_json = json.dumps({"action": "click", "target": "100,200"})

    draft_yaml = build_recipe_draft([ev])
    parsed = yaml.safe_load(draft_yaml)
    step = parsed["steps"][0]
    assert "description" in step
    assert "unstable" in step["description"]
