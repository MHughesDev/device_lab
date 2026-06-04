"""settings_service.py — Typed settings service for Phase 12 (root & cloud infra settings)."""
from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from app.models import AppSetting, AuditEvent

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, dict[str, Any]] = {
    "cloud": {
        "credential_source": "env",   # env|profile|role
        "default_region": "us-east-1",
        "default_vpc_id": None,
        "default_subnet_id": None,
        "linux_instance_type": "t3.medium",
        "android_instance_type": "c8i.xlarge",
        "windows_instance_type": "t3.large",
        "macos_instance_type": "mac2.metal",
        "artifact_bucket": None,
        "stun_url": None,
        "turn_url": None,
        "turn_username": None,
        "turn_credential": None,
        "credential_profile": None,
        "credential_role_arn": None,
    },
    "host": {
        "device_ram_budget_mb": None,    # None = auto from OS
        "device_cpu_budget_cores": None, # None = auto
        "headroom_pct": 20,
        "storage_path": "/var/lib/devicelab/images",
        "placement_policy": "local_first",  # local_first|cloud_first|local_only
        "max_devices": 10,
    },
    "streaming": {
        "default_codec": "h264",
        "local_bitrate_kbps": 8000,
        "cloud_bitrate_kbps": 4000,
        "default_profile": "smooth",  # smooth|sharp_text
        "max_concurrent_streams": 8,
        "webcodecs_canvas_default": False,
    },
    "mcp": {
        "global_enabled": True,
        "default_exposure": True,
        "default_role": "observe",  # observe|test|operate|admin
        "token_ttl_minutes": 60,
        "bind_host": "127.0.0.1",  # MUST be loopback
    },
    "manifests": {
        "export_dir": "/var/lib/devicelab/manifests/export",
        "import_dir": "/var/lib/devicelab/manifests/import",
        "max_count": 100,
        "retention_days": 90,
        "validation_strictness": "standard",  # standard|strict|permissive
    },
    "security": {
        "audit_log_path": "/var/lib/devicelab/audit.jsonl",
        "keyring_backend": "auto",  # auto|system|file
        "dangerous_mode": False,
        "log_redaction_patterns": [".*PASSWORD.*", ".*SECRET.*", ".*TOKEN.*", ".*KEY.*", ".*CREDENTIAL.*"],
    },
}

VALID_GROUPS: set[str] = set(DEFAULTS.keys())

# Keys whose values are secrets — stored via keyring, returned as "***"
SECRET_KEYS: set[str] = {
    "turn_url", "turn_username", "turn_credential",
    "credential_profile", "credential_role_arn",
}

_LOOPBACK_HOSTS = {"127.0.0.1", "::1"}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate(group: str, values: dict[str, Any]) -> None:
    """Raise ValueError if any value violates a known constraint."""
    if group == "mcp":
        bind_host = values.get("bind_host")
        if bind_host is not None and bind_host not in _LOOPBACK_HOSTS:
            raise ValueError("MCP bind host must be loopback")

    if group == "streaming":
        profile = values.get("default_profile")
        if profile is not None and profile not in ("smooth", "sharp_text"):
            raise ValueError(f"streaming.default_profile must be 'smooth' or 'sharp_text', got {profile!r}")

    if group == "host":
        headroom = values.get("headroom_pct")
        if headroom is not None and not (0 <= headroom <= 50):
            raise ValueError(f"host.headroom_pct must be 0–50, got {headroom}")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _load_rows(db: Session, workspace_id: uuid.UUID, group: str) -> dict[str, AppSetting]:
    """Return stored AppSetting rows for the given group keyed by setting key."""
    rows = db.exec(
        select(AppSetting).where(
            AppSetting.workspace_id == workspace_id,
            AppSetting.group == group,
        )
    ).all()
    return {row.key: row for row in rows}


def _decode_value(raw: str | None) -> Any:
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def _encode_value(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value)


def _emit_audit(db: Session, workspace_id: uuid.UUID, group: str, keys: list[str]) -> None:
    """Append a settings.update audit event using the proper HMAC chain."""
    from app.core.audit_log import append_event
    append_event(
        db,
        workspace_id=workspace_id,
        actor="operator",
        action="settings.update",
        target_type="settings",
        target_id=str(workspace_id),
        metadata={"group": group, "keys": keys},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_group(db: Session, workspace_id: uuid.UUID, group: str) -> dict[str, Any]:
    """Return merged (defaults + stored) values for a group.

    Secret values are returned as the '***' sentinel — never the raw secret.
    """
    if group not in VALID_GROUPS:
        raise ValueError(f"Unknown settings group: {group!r}")

    defaults = dict(DEFAULTS[group])
    rows = _load_rows(db, workspace_id, group)

    merged: dict[str, Any] = {}
    for key, default_val in defaults.items():
        if key in rows:
            row = rows[key]
            if row.is_secret_ref:
                merged[key] = "***"
            else:
                merged[key] = _decode_value(row.value)
        else:
            # Secret defaults are masked too (they're None by default, so safe)
            if key in SECRET_KEYS:
                # If the key has a stored row it's handled above; if no row, show None
                merged[key] = default_val
            else:
                merged[key] = default_val

    return merged


def update_group(db: Session, workspace_id: uuid.UUID, group: str, values: dict[str, Any]) -> dict[str, Any]:
    """Persist values for a group.

    Validates group name and business rules. Secret keys are stored via keyring
    with is_secret_ref=True. Emits an audit event. Returns the updated group view.
    """
    if group not in VALID_GROUPS:
        raise ValueError(f"Unknown settings group: {group!r}")

    _validate(group, values)

    rows = _load_rows(db, workspace_id, group)

    for key, value in values.items():
        is_secret = key in SECRET_KEYS

        if is_secret and value is not None and value != "***":
            # Store via keyring; set the row to hold just the ref name
            import keyring
            service = "devicelab-settings"
            keyring.set_password(service, key, str(value))
            encoded_value = key  # the ref name
            secret_ref_flag = True
        elif is_secret and value == "***":
            # Client sent back the sentinel — don't overwrite the stored secret
            continue
        else:
            encoded_value = _encode_value(value)
            secret_ref_flag = False

        if key in rows:
            row = rows[key]
            row.value = encoded_value
            row.is_secret_ref = secret_ref_flag
            row.updated_at = datetime.now(UTC)
            db.add(row)
        else:
            row = AppSetting(
                workspace_id=workspace_id,
                group=group,
                key=key,
                value=encoded_value,
                is_secret_ref=secret_ref_flag,
                updated_at=datetime.now(UTC),
            )
            db.add(row)

    db.flush()  # write rows before audit so they're visible in the same transaction
    _emit_audit(db, workspace_id, group, list(values.keys()))
    db.commit()

    return get_group(db, workspace_id, group)


def get_all(db: Session, workspace_id: uuid.UUID) -> dict[str, dict[str, Any]]:
    """Return all groups merged (defaults + stored values)."""
    return {group: get_group(db, workspace_id, group) for group in VALID_GROUPS}
