# services/manifest_spec.py — Manifest spec format + validation (Phase 10, task 10-03)
"""
JSON Schema validation for DeviceManifest spec_json payloads.

The spec is a family-conditional JSON object. Common fields are validated for all
families; install_steps types are validated per-step.

Reference: docs/design/manifest-spec.json
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)

# Install step types supported per family
_STEP_TYPES_BY_FAMILY: dict[str, set[str]] = {
    "linux":   {"apt", "pip", "npm_global", "shell", "env_vars"},
    "android": {"adb_install", "adb_shell", "shell"},
    "windows": {"winget_install", "msi_install", "powershell", "shell"},
    "macos":   {"brew", "mas_install", "shell"},
    "ios_sim": {"xcrun_install", "shell"},
}

_ALL_STEP_TYPES: set[str] = {t for types in _STEP_TYPES_BY_FAMILY.values() for t in types}


class ManifestValidationError(ValueError):
    """Raised when a manifest spec fails schema validation."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


def validate(spec_json: str, family: str) -> dict:
    """Validate and parse a spec_json string for the given device family.

    Returns the parsed spec dict on success.
    Raises ManifestValidationError with field-level context on failure.
    """
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(f"spec_json is not valid JSON: {exc}", field="spec_json") from exc

    if not isinstance(spec, dict):
        raise ManifestValidationError("spec_json must be a JSON object", field="spec_json")

    allowed_families = set(_STEP_TYPES_BY_FAMILY.keys())
    if family not in allowed_families:
        raise ManifestValidationError(
            f"Unknown family '{family}'. Must be one of: {sorted(allowed_families)}",
            field="family",
        )

    # Validate env_vars
    if "env_vars" in spec:
        if not isinstance(spec["env_vars"], dict):
            raise ManifestValidationError("env_vars must be an object", field="env_vars")
        for k, v in spec["env_vars"].items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ManifestValidationError(
                    f"env_vars keys and values must be strings; got {k!r}:{v!r}", field="env_vars"
                )

    # Validate install_steps
    steps = spec.get("install_steps", [])
    if not isinstance(steps, list):
        raise ManifestValidationError("install_steps must be an array", field="install_steps")

    allowed_types = _STEP_TYPES_BY_FAMILY.get(family, set())
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ManifestValidationError(
                f"install_steps[{i}] must be an object", field=f"install_steps[{i}]"
            )
        step_type = step.get("type")
        if step_type is None:
            raise ManifestValidationError(
                f"install_steps[{i}] missing required 'type' field",
                field=f"install_steps[{i}].type",
            )
        if step_type not in allowed_types:
            raise ManifestValidationError(
                f"install_steps[{i}].type '{step_type}' is not valid for family '{family}'. "
                f"Allowed: {sorted(allowed_types)}",
                field=f"install_steps[{i}].type",
            )
        _validate_step_fields(step, step_type, i)

    # Validate startup_commands
    cmds = spec.get("startup_commands", [])
    if not isinstance(cmds, list):
        raise ManifestValidationError("startup_commands must be an array", field="startup_commands")
    for i, cmd in enumerate(cmds):
        if not isinstance(cmd, str):
            raise ManifestValidationError(
                f"startup_commands[{i}] must be a string", field=f"startup_commands[{i}]"
            )

    return spec


def _validate_step_fields(step: dict, step_type: str, idx: int) -> None:
    """Validate fields specific to each install step type."""
    field_prefix = f"install_steps[{idx}]"

    if step_type == "apt":
        pkgs = step.get("packages")
        if pkgs is None or not isinstance(pkgs, list) or not pkgs:
            raise ManifestValidationError(f"{field_prefix}.packages required (non-empty list)", field=f"{field_prefix}.packages")

    elif step_type in ("pip", "npm_global", "brew"):
        pkgs = step.get("packages")
        if pkgs is None or not isinstance(pkgs, list) or not pkgs:
            raise ManifestValidationError(f"{field_prefix}.packages required (non-empty list)", field=f"{field_prefix}.packages")

    elif step_type == "shell":
        cmd = step.get("command")
        if not cmd or not isinstance(cmd, str):
            raise ManifestValidationError(f"{field_prefix}.command required (string)", field=f"{field_prefix}.command")

    elif step_type == "adb_install":
        apk = step.get("apk_path")
        if not apk or not isinstance(apk, str):
            raise ManifestValidationError(f"{field_prefix}.apk_path required (string)", field=f"{field_prefix}.apk_path")

    elif step_type == "winget_install":
        pkg_id = step.get("package_id")
        if not pkg_id or not isinstance(pkg_id, str):
            raise ManifestValidationError(f"{field_prefix}.package_id required (string)", field=f"{field_prefix}.package_id")

    elif step_type == "xcrun_install":
        app_path = step.get("app_path")
        if not app_path or not isinstance(app_path, str):
            raise ManifestValidationError(f"{field_prefix}.app_path required (string)", field=f"{field_prefix}.app_path")
