# tests/services/test_manifest_bootstrap.py — Phase 10 manifest→pypyr translation tests
from __future__ import annotations

import json
import pytest

from app.services.manifest_bootstrap import to_pypyr_pipeline, TranslationError


def test_apt_steps_translate_to_pypyr():
    spec_json = json.dumps({
        "install_steps": [{"type": "apt", "packages": ["git", "curl"]}]
    })
    pipeline = to_pypyr_pipeline(spec_json, "linux")
    assert "apt_install" in pipeline
    assert "git" in pipeline


def test_shell_steps_use_pypyr_cmd():
    spec_json = json.dumps({
        "install_steps": [{"type": "shell", "command": "echo hello"}]
    })
    pipeline = to_pypyr_pipeline(spec_json, "linux")
    assert "pypyr.steps.cmd" in pipeline
    assert "echo hello" in pipeline


def test_pip_steps_translate():
    spec_json = json.dumps({
        "install_steps": [{"type": "pip", "packages": ["requests"]}]
    })
    pipeline = to_pypyr_pipeline(spec_json, "linux")
    assert "pip_install" in pipeline


def test_npm_global_translates():
    spec_json = json.dumps({
        "install_steps": [{"type": "npm_global", "packages": ["pnpm"]}]
    })
    pipeline = to_pypyr_pipeline(spec_json, "linux")
    assert "npm_global_install" in pipeline


def test_winget_install_translates():
    spec_json = json.dumps({
        "install_steps": [{"type": "winget_install", "package_id": "Git.Git"}]
    })
    pipeline = to_pypyr_pipeline(spec_json, "windows")
    assert "winget_install" in pipeline


def test_brew_translates():
    spec_json = json.dumps({
        "install_steps": [{"type": "brew", "packages": ["wget"]}]
    })
    pipeline = to_pypyr_pipeline(spec_json, "macos")
    assert "brew_install" in pipeline


def test_env_vars_translated_first():
    spec_json = json.dumps({
        "env_vars": {"NODE_ENV": "test"},
        "install_steps": [],
    })
    pipeline = to_pypyr_pipeline(spec_json, "linux")
    assert "set_env_vars" in pipeline


def test_startup_commands_at_end():
    spec_json = json.dumps({
        "install_steps": [],
        "startup_commands": ["Xvfb :0 &"],
    })
    pipeline = to_pypyr_pipeline(spec_json, "linux")
    assert "Xvfb :0 &" in pipeline


def test_empty_spec_produces_valid_pipeline():
    pipeline = to_pypyr_pipeline("{}", "linux")
    assert "steps" in pipeline


def test_invalid_json_raises():
    with pytest.raises(TranslationError):
        to_pypyr_pipeline("not json", "linux")


def test_unknown_step_type_raises_translation_error():
    spec_json = json.dumps({
        "install_steps": [{"type": "totally_unknown_step"}]
    })
    with pytest.raises(TranslationError, match="no pypyr translation"):
        to_pypyr_pipeline(spec_json, "linux")
