# guardrail.py — CostGuardrail service: evaluate device actions against workspace cost policies
from __future__ import annotations
from decimal import Decimal
import uuid
from sqlmodel import Session, select
from app.models import CostPolicy, Device, GuardrailResult
from app.core.audit_log import append_event


COST_CLASS: dict[str, str] = {
    "provision": "moderate",
    "start": "cheap",
    "snapshot": "moderate",
    "fork": "expensive",
    "recipe_long": "moderate",
    "terminate": "free",
    "stop": "free",
}


def check(
    db: Session,
    workspace_id: uuid.UUID,
    action: str,
    device: Device,
    estimated_cost_usd: Decimal,
    current_spend_usd: Decimal,
) -> GuardrailResult:
    """Evaluate action against workspace cost policy.

    Appends an AuditEvent for expensive-class or blocked decisions.
    Returns GuardrailResult with decision = 'allow' | 'warn' | 'block'.
    """
    policy = _load_policy(db, workspace_id, device)

    projected_total = current_spend_usd + estimated_cost_usd

    soft_cap = Decimal(policy.soft_cap_usd) if policy and policy.soft_cap_usd else None
    hard_cap = Decimal(policy.hard_cap_usd) if policy and policy.hard_cap_usd else None

    if hard_cap is not None and projected_total >= hard_cap:
        decision = "block"
        message = f"Projected spend ${projected_total} exceeds hard cap ${hard_cap}"
        override_available = policy.override_requires_dangerous_mode if policy else False
    elif soft_cap is not None and projected_total >= soft_cap:
        decision = "warn"
        message = f"Projected spend ${projected_total} exceeds soft cap ${soft_cap}"
        override_available = False
    else:
        decision = "allow"
        message = "Within budget"
        override_available = False

    cost_class = COST_CLASS.get(action, "moderate")
    if decision == "block" or cost_class == "expensive":
        append_event(
            db,
            workspace_id=workspace_id,
            actor="guardrail",
            action="cost_check",
            target_type="Device",
            target_id=str(device.id),
            decision=decision,
            metadata={
                "action": action,
                "estimated_cost_usd": str(estimated_cost_usd),
                "current_spend_usd": str(current_spend_usd),
                "projected_total_usd": str(projected_total),
                "soft_cap_usd": str(soft_cap) if soft_cap else None,
                "hard_cap_usd": str(hard_cap) if hard_cap else None,
            },
        )

    return GuardrailResult(
        decision=decision,
        message=message,
        current_spend_usd=str(current_spend_usd),
        soft_cap_usd=str(soft_cap) if soft_cap else None,
        hard_cap_usd=str(hard_cap) if hard_cap else None,
        override_available=override_available,
        policy_id=str(policy.id) if policy else None,
    )


def _load_policy(db: Session, workspace_id: uuid.UUID, device: Device) -> CostPolicy | None:
    """Return most-specific policy: device > template > family > workspace."""
    device_id_str = str(device.id)
    template_id_str = str(device.template_id) if hasattr(device, "template_id") and device.template_id else None
    family_str = device.family if hasattr(device, "family") else None

    candidates = db.exec(
        select(CostPolicy).where(CostPolicy.workspace_id == workspace_id)
    ).all()

    for scope, scope_id in [
        ("device", device_id_str),
        ("template", template_id_str),
        ("family", family_str),
        ("workspace", None),
    ]:
        for p in candidates:
            if p.scope == scope:
                if scope == "workspace" or p.scope_id == scope_id:
                    return p
    return None


class GuardrailBlocked(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
