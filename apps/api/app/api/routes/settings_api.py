"""settings_api.py — REST endpoints for Phase 12 root & cloud infra settings."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import SettingsGroupUpdate, Workspace
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_workspace(db) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialised")
    return ws


@router.get("/", response_model=dict[str, dict[str, Any]])
def get_all_settings(db: SessionDep) -> dict[str, dict[str, Any]]:
    """Return all settings groups merged with defaults."""
    ws = _get_workspace(db)
    return settings_service.get_all(db, ws.id)


@router.get("/{group}", response_model=dict[str, Any])
def get_settings_group(group: str, db: SessionDep) -> dict[str, Any]:
    """Return a single settings group merged with defaults."""
    ws = _get_workspace(db)
    try:
        return settings_service.get_group(db, ws.id, group)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{group}", response_model=dict[str, Any])
def update_settings_group(group: str, body: SettingsGroupUpdate, db: SessionDep) -> dict[str, Any]:
    """Persist settings for a group. Validates constraints. Emits audit event."""
    ws = _get_workspace(db)
    try:
        return settings_service.update_group(db, ws.id, group, body.values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/cloud/test-connection", response_model=dict[str, Any])
def test_cloud_connection(db: SessionDep) -> dict[str, Any]:
    """Validate AWS credentials by calling STS GetCallerIdentity."""
    ws = _get_workspace(db)

    try:
        cloud = settings_service.get_group(db, ws.id, "cloud")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        import boto3

        credential_source = cloud.get("credential_source", "env")
        region = cloud.get("default_region", "us-east-1") or "us-east-1"

        boto_kwargs: dict[str, Any] = {"region_name": region}

        if credential_source == "profile":
            # Resolve the actual profile name from keyring if stored as secret ref
            profile_name = _resolve_secret_if_needed(db, ws.id, "credential_profile")
            if profile_name:
                import botocore.session
                session = boto3.Session(profile_name=profile_name, region_name=region)
                sts = session.client("sts")
            else:
                sts = boto3.client("sts", **boto_kwargs)
        elif credential_source == "role":
            role_arn = _resolve_secret_if_needed(db, ws.id, "credential_role_arn")
            if role_arn:
                base_sts = boto3.client("sts", **boto_kwargs)
                assumed = base_sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="devicelab-preflight",
                )
                creds = assumed["Credentials"]
                sts = boto3.client(
                    "sts",
                    region_name=region,
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                )
            else:
                sts = boto3.client("sts", **boto_kwargs)
        else:
            # env — boto3 picks up AWS_ACCESS_KEY_ID etc. from environment
            sts = boto3.client("sts", **boto_kwargs)

        identity = sts.get_caller_identity()
        return {
            "status": "ok",
            "detail": (
                f"Connected as {identity.get('Arn', 'unknown')} "
                f"(account {identity.get('Account', 'unknown')})"
            ),
        }

    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _resolve_secret_if_needed(db, workspace_id, key: str) -> str | None:
    """If the setting is stored as a secret ref, resolve it via keyring; else return the raw value."""
    from sqlmodel import select
    from app.models import AppSetting

    row = db.exec(
        select(AppSetting).where(
            AppSetting.workspace_id == workspace_id,
            AppSetting.group == "cloud",
            AppSetting.key == key,
        )
    ).first()

    if row is None:
        return None

    if row.is_secret_ref:
        import keyring
        return keyring.get_password("devicelab-settings", key)

    try:
        import json
        return json.loads(row.value) if row.value else None
    except Exception:
        return row.value
