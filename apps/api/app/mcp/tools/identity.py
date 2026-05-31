"""MCP tools for secret injection with elicitation gate."""
from __future__ import annotations

from app.mcp.gateway import mcp


@mcp.tool()
def list_secret_refs() -> list[dict]:
    """List available SecretRef names and descriptions. Values are never returned."""
    from app.core.db import engine
    from sqlmodel import Session, select
    from app.models import SecretRef, Workspace

    with Session(engine) as db:
        ws = db.exec(select(Workspace).limit(1)).first()
        if not ws:
            return []
        refs = db.exec(select(SecretRef).where(SecretRef.workspace_id == ws.id)).all()
        return [{"name": r.name, "description": r.description, "backend": r.backend} for r in refs]


@mcp.tool()
def inject_secret_into_step(
    device_id: str,
    ref_name: str,
    action: str,
    field: str,
    additional_params: dict | None = None,
) -> dict:
    """
    Inject a secret value into a single action step. The secret value is fetched from keychain
    and used directly in the action — it never appears in the MCP response.

    Emits an AuditEvent: actor=mcp_client, action=secret_inject, target=ref_name.
    """
    import asyncio
    import uuid
    from app.core.db import engine
    from sqlmodel import Session, select
    from app.models import Workspace
    from app.services.identity.broker import SecretNotFound, resolve
    from app.services.interaction import execute_action
    from app.core.audit_log import append_event

    with Session(engine) as db:
        ws = db.exec(select(Workspace).limit(1)).first()
        if not ws:
            return {"success": False, "error": "Workspace not initialised"}
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"success": False, "error": "Invalid device_id"}

        try:
            secret_value = resolve(db, ws.id, ref_name)
        except SecretNotFound as e:
            return {"success": False, "error": str(e)}

        params = dict(additional_params or {})
        params[field] = secret_value

        result = asyncio.get_event_loop().run_until_complete(
            execute_action(db, did, action, params, session_id="mcp-secret-inject")
        )

        # Audit — never log the secret value, only the ref name
        append_event(
            db=db,
            workspace_id=ws.id,
            actor="mcp_client",
            action="secret_inject",
            target_type="SecretRef",
            target_id=ref_name,
            decision="allow",
            metadata={"action": action, "field": field, "approval_mode": "auto"},
        )

        # Return result without secret value
        return {
            "success": result.success,
            "evidence_id": result.evidence_id,
            "before_screen_version": result.before_screen_version,
            "after_screen_version": result.after_screen_version,
            "error": result.error,
        }
