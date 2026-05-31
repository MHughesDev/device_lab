import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.models import CostPolicy, Device, Workspace


def _engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


def _make_workspace(db: Session) -> Workspace:
    ws = Workspace(id=uuid.uuid4(), name="test-ws", created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def _make_device(db: Session, workspace_id: uuid.UUID) -> Device:
    device = Device(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        family="linux",
        state="requested",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def _make_policy(db: Session, workspace_id: uuid.UUID, soft=None, hard=None) -> CostPolicy:
    policy = CostPolicy(
        workspace_id=workspace_id,
        soft_cap_usd=soft,
        hard_cap_usd=hard,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def test_allow_below_soft_cap():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id)
        _make_policy(db, ws.id, soft="100.00", hard="200.00")
        from app.services.cost.guardrail import check
        with patch("app.services.cost.guardrail.append_event"):
            result = check(db, ws.id, "start", device, Decimal("10"), Decimal("50"))
    assert result.decision == "allow"


def test_warn_at_soft_cap():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id)
        _make_policy(db, ws.id, soft="100.00", hard="200.00")
        from app.services.cost.guardrail import check
        with patch("app.services.cost.guardrail.append_event"):
            result = check(db, ws.id, "start", device, Decimal("10"), Decimal("95"))
    assert result.decision == "warn"


def test_block_at_hard_cap():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id)
        _make_policy(db, ws.id, soft="100.00", hard="200.00")
        from app.services.cost.guardrail import check
        with patch("app.services.cost.guardrail.append_event") as mock_audit:
            result = check(db, ws.id, "start", device, Decimal("10"), Decimal("195"))
    assert result.decision == "block"


def test_no_policy_allows():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id)
        from app.services.cost.guardrail import check
        with patch("app.services.cost.guardrail.append_event"):
            result = check(db, ws.id, "start", device, Decimal("10"), Decimal("9999"))
    assert result.decision == "allow"


def test_block_appends_audit_event():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id)
        _make_policy(db, ws.id, hard="50.00")
        from app.services.cost.guardrail import check
        with patch("app.services.cost.guardrail.append_event") as mock_audit:
            result = check(db, ws.id, "start", device, Decimal("10"), Decimal("45"))
        mock_audit.assert_called_once()
    assert result.decision == "block"


def test_override_available_flag():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id)
        _make_policy(db, ws.id, hard="50.00")
        from app.services.cost.guardrail import check
        with patch("app.services.cost.guardrail.append_event"):
            result = check(db, ws.id, "start", device, Decimal("10"), Decimal("45"))
    assert result.override_available is True
