"""Recipe validation — checks schema, capability requirements, and secret ref syntax."""
from __future__ import annotations

import yaml
from pydantic import ValidationError

from app.services.recipes.schema import RecipeSchema

DANGEROUS_ACTIONS = {"raw_shell", "file_delete", "process_kill"}


class RecipeValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def parse_and_validate(yaml_content: str, device_family: str | None = None) -> RecipeSchema:
    """Parse recipe YAML and validate structure. Raises RecipeValidationError on failure."""
    errors: list[str] = []

    try:
        raw = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise RecipeValidationError([f"YAML parse error: {e}"])

    if not isinstance(raw, dict):
        raise RecipeValidationError(["Recipe must be a YAML mapping"])

    try:
        recipe = RecipeSchema.model_validate(raw)
    except ValidationError as e:
        raise RecipeValidationError([str(err["msg"]) for err in e.errors()])

    # Family compatibility
    if device_family and recipe.families and device_family not in recipe.families:
        errors.append(f"Recipe families {recipe.families} does not include device family '{device_family}'")

    # Dangerous steps must be declared
    for step in recipe.steps:
        if step.action in DANGEROUS_ACTIONS and not step.dangerous:
            errors.append(f"Step '{step.id}': action '{step.action}' is dangerous — set dangerous: true and ensure DANGEROUS_MODE=true")

    # Secret ref inputs must have a ref
    for input_name, inp in recipe.inputs.items():
        if inp.type == "secret_ref" and not inp.ref:
            errors.append(f"Input '{input_name}': secret_ref type requires a 'ref' field")

    if errors:
        raise RecipeValidationError(errors)

    return recipe
