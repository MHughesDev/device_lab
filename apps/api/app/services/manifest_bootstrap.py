# services/manifest_bootstrap.py — Manifest → pypyr pipeline translation (Phase 10, task 10-09)
"""
Translates a DeviceManifest's install_steps into a pypyr YAML pipeline that
runs during the `bootstrapping_agent` FSM phase.

The pypyr pipeline is a YAML string that pypyr's runner can execute directly.
Each install step type maps to a DeviceLab-provided pypyr step module.

Step type → pypyr step module:
  apt           → devicelab.steps.apt_install
  pip           → devicelab.steps.pip_install
  npm_global    → devicelab.steps.npm_global_install
  shell         → pypyr.steps.cmd
  env_vars      → devicelab.steps.set_env_vars
  adb_install   → devicelab.steps.adb_install
  adb_shell     → devicelab.steps.adb_shell
  winget_install → devicelab.steps.winget_install
  msi_install   → devicelab.steps.msi_install
  powershell    → devicelab.steps.powershell_run
  brew          → devicelab.steps.brew_install
  mas_install   → devicelab.steps.mas_install
  xcrun_install → devicelab.steps.simctl_install

Translation only — execution is the FSM bootstrapping_agent hook.
"""
from __future__ import annotations

import json
import logging

import yaml  # type: ignore

log = logging.getLogger(__name__)


class TranslationError(ValueError):
    """Raised when a step cannot be translated to a pypyr step."""


def to_pypyr_pipeline(spec_json: str, family: str) -> str:
    """Convert a manifest spec_json into a pypyr YAML pipeline string.

    Returns a YAML string that can be written to a .yaml file and executed with:
        pypyr <pipeline_path>
    """
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError as exc:
        raise TranslationError(f"Invalid spec_json: {exc}") from exc

    steps = []

    # Apply env_vars first (if present as a top-level field or step)
    env_vars = spec.get("env_vars", {})
    if env_vars:
        steps.append({
            "name": "devicelab.steps.set_env_vars",
            "in": {"env_vars": env_vars},
            "comment": "Set environment variables from manifest",
        })

    # Translate install_steps
    for i, step in enumerate(spec.get("install_steps", [])):
        step_type = step.get("type")
        pypyr_step = _translate_step(step, step_type, i, family)
        if pypyr_step:
            steps.append(pypyr_step)

    # Apply startup_commands at end
    for cmd in spec.get("startup_commands", []):
        steps.append({
            "name": "pypyr.steps.cmd",
            "in": {"cmd": cmd},
            "comment": "Startup command",
        })

    pipeline = {
        "steps": steps if steps else [{"name": "pypyr.steps.echo", "in": {"echoMe": "No install steps."}}],
    }
    return yaml.dump(pipeline, default_flow_style=False, allow_unicode=True)


def _translate_step(step: dict, step_type: str, idx: int, family: str) -> dict | None:
    """Translate a single install step to a pypyr step dict."""
    if step_type == "apt":
        packages = step.get("packages", [])
        return {
            "name": "devicelab.steps.apt_install",
            "in": {"packages": packages},
        }

    if step_type == "pip":
        packages = step.get("packages", [])
        return {
            "name": "devicelab.steps.pip_install",
            "in": {"packages": packages},
        }

    if step_type == "npm_global":
        packages = step.get("packages", [])
        return {
            "name": "devicelab.steps.npm_global_install",
            "in": {"packages": packages},
        }

    if step_type == "shell":
        return {
            "name": "pypyr.steps.cmd",
            "in": {"cmd": step["command"]},
        }

    if step_type == "env_vars":
        return {
            "name": "devicelab.steps.set_env_vars",
            "in": {"env_vars": step.get("vars", {})},
        }

    if step_type == "adb_install":
        return {
            "name": "devicelab.steps.adb_install",
            "in": {"apk_path": step["apk_path"]},
        }

    if step_type == "adb_shell":
        return {
            "name": "devicelab.steps.adb_shell",
            "in": {"command": step["command"]},
        }

    if step_type == "winget_install":
        return {
            "name": "devicelab.steps.winget_install",
            "in": {"package_id": step["package_id"], "version": step.get("version")},
        }

    if step_type == "msi_install":
        return {
            "name": "devicelab.steps.msi_install",
            "in": {"msi_path": step["msi_path"], "args": step.get("args", "")},
        }

    if step_type == "powershell":
        return {
            "name": "devicelab.steps.powershell_run",
            "in": {"script": step["script"]},
        }

    if step_type == "brew":
        packages = step.get("packages", [])
        return {
            "name": "devicelab.steps.brew_install",
            "in": {"packages": packages},
        }

    if step_type == "mas_install":
        return {
            "name": "devicelab.steps.mas_install",
            "in": {"app_id": step["app_id"]},
        }

    if step_type == "xcrun_install":
        return {
            "name": "devicelab.steps.simctl_install",
            "in": {"app_path": step["app_path"]},
        }

    raise TranslationError(
        f"install_steps[{idx}].type '{step_type}' has no pypyr translation for family '{family}'"
    )
