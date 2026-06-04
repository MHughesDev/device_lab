# tests/services/test_manifest_spec.py — Phase 10 manifest spec validation tests
from __future__ import annotations

import json
import pytest

from app.services.manifest_spec import validate, ManifestValidationError


def test_valid_empty_spec_passes():
    spec = validate("{}", "linux")
    assert isinstance(spec, dict)


def test_valid_apt_step_passes():
    spec_json = json.dumps({
        "install_steps": [{"type": "apt", "packages": ["git", "curl"]}]
    })
    spec = validate(spec_json, "linux")
    assert spec["install_steps"][0]["packages"] == ["git", "curl"]


def test_valid_pip_step_passes():
    spec_json = json.dumps({
        "install_steps": [{"type": "pip", "packages": ["pytest==7.4.0"]}]
    })
    spec = validate(spec_json, "linux")
    assert spec["install_steps"][0]["type"] == "pip"


def test_valid_shell_step_passes():
    spec_json = json.dumps({
        "install_steps": [{"type": "shell", "command": "echo hello"}]
    })
    spec = validate(spec_json, "linux")
    assert spec["install_steps"][0]["command"] == "echo hello"


def test_valid_android_adb_install_passes():
    spec_json = json.dumps({
        "install_steps": [{"type": "adb_install", "apk_path": "/apks/myapp.apk"}]
    })
    spec = validate(spec_json, "android")
    assert spec["install_steps"][0]["apk_path"] == "/apks/myapp.apk"


def test_valid_windows_winget_passes():
    spec_json = json.dumps({
        "install_steps": [{"type": "winget_install", "package_id": "Git.Git"}]
    })
    spec = validate(spec_json, "windows")
    assert spec["install_steps"][0]["package_id"] == "Git.Git"


def test_valid_brew_step_passes():
    spec_json = json.dumps({
        "install_steps": [{"type": "brew", "packages": ["wget", "jq"]}]
    })
    spec = validate(spec_json, "macos")
    assert spec["install_steps"][0]["packages"] == ["wget", "jq"]


def test_valid_xcrun_install_passes():
    spec_json = json.dumps({
        "install_steps": [{"type": "xcrun_install", "app_path": "/apps/MyApp.app"}]
    })
    spec = validate(spec_json, "ios_sim")
    assert spec["install_steps"][0]["app_path"] == "/apps/MyApp.app"


def test_invalid_json_raises():
    with pytest.raises(ManifestValidationError, match="not valid JSON"):
        validate("not json", "linux")


def test_non_object_raises():
    with pytest.raises(ManifestValidationError, match="JSON object"):
        validate("[1, 2, 3]", "linux")


def test_unknown_family_raises():
    with pytest.raises(ManifestValidationError, match="Unknown family"):
        validate("{}", "commodore64")


def test_unknown_install_type_raises():
    spec_json = json.dumps({
        "install_steps": [{"type": "chocolatey_install", "package_id": "git"}]
    })
    with pytest.raises(ManifestValidationError, match="not valid for family"):
        validate(spec_json, "linux")


def test_missing_packages_in_apt_raises():
    spec_json = json.dumps({
        "install_steps": [{"type": "apt", "packages": []}]
    })
    with pytest.raises(ManifestValidationError, match="packages"):
        validate(spec_json, "linux")


def test_missing_command_in_shell_raises():
    spec_json = json.dumps({
        "install_steps": [{"type": "shell"}]
    })
    with pytest.raises(ManifestValidationError, match="command"):
        validate(spec_json, "linux")


def test_family_conditional_android_step_rejected_on_linux():
    spec_json = json.dumps({
        "install_steps": [{"type": "adb_install", "apk_path": "/apks/app.apk"}]
    })
    with pytest.raises(ManifestValidationError, match="not valid for family"):
        validate(spec_json, "linux")


def test_env_vars_must_be_object():
    spec_json = json.dumps({"env_vars": ["not", "a", "dict"]})
    with pytest.raises(ManifestValidationError, match="env_vars"):
        validate(spec_json, "linux")


def test_startup_commands_must_be_list():
    spec_json = json.dumps({"startup_commands": "bad"})
    with pytest.raises(ManifestValidationError, match="startup_commands"):
        validate(spec_json, "linux")
