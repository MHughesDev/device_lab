import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.core import audit_log
from app.models import AuditEvent


def _make_workspace_id() -> uuid.UUID:
    return uuid.uuid4()


def _fake_event(
    workspace_id: uuid.UUID,
    actor: str = "system",
    action: str = "test.action",
    prev_hash: str = "genesis",
    hash_val: str | None = None,
    created_at: datetime | None = None,
) -> AuditEvent:
    entry = {
        "actor": actor,
        "action": action,
        "target_type": "device",
        "target_id": str(uuid.uuid4()),
        "decision": "allow",
        "metadata": {},
        "timestamp": (created_at or datetime.now(UTC)).isoformat(),
    }
    computed = audit_log._compute_hash(entry, prev_hash)
    return AuditEvent(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        actor=actor,
        action=action,
        target_type="device",
        target_id=entry["target_id"],
        decision="allow",
        metadata_json="{}",
        created_at=created_at or datetime.now(UTC),
        hash=hash_val or computed,
        prev_hash=prev_hash,
    )


class TestComputeHash:
    def test_deterministic(self) -> None:
        entry = {"actor": "a", "action": "b", "target_type": "c", "target_id": "d", "decision": "allow", "metadata": {}, "timestamp": "t"}
        h1 = audit_log._compute_hash(entry, "genesis")
        h2 = audit_log._compute_hash(entry, "genesis")
        assert h1 == h2

    def test_different_prev_hash_changes_result(self) -> None:
        entry = {"actor": "a", "action": "b", "target_type": "c", "target_id": "d", "decision": "allow", "metadata": {}, "timestamp": "t"}
        h1 = audit_log._compute_hash(entry, "genesis")
        h2 = audit_log._compute_hash(entry, "other")
        assert h1 != h2

    def test_hash_is_hex_string(self) -> None:
        entry = {"actor": "a", "action": "b", "target_type": "c", "target_id": "d", "decision": "allow", "metadata": {}, "timestamp": "t"}
        h = audit_log._compute_hash(entry, "genesis")
        assert len(h) == 64
        int(h, 16)  # must be valid hex


class TestVerifyChain:
    def test_empty_chain_is_valid(self) -> None:
        db = MagicMock()
        db.exec.return_value.all.return_value = []
        wid = _make_workspace_id()
        assert audit_log.verify_chain(db, wid) is True

    def test_valid_three_event_chain(self) -> None:
        wid = _make_workspace_id()
        e1 = _fake_event(wid, prev_hash="genesis")
        e2 = _fake_event(wid, prev_hash=e1.hash)
        e3 = _fake_event(wid, prev_hash=e2.hash)

        db = MagicMock()
        db.exec.return_value.all.return_value = [e1, e2, e3]
        assert audit_log.verify_chain(db, wid) is True

    def test_tampered_hash_detected(self) -> None:
        wid = _make_workspace_id()
        e1 = _fake_event(wid, prev_hash="genesis")
        # tamper: set e1.hash to wrong value
        e1.hash = "deadbeef" * 8

        db = MagicMock()
        db.exec.return_value.all.return_value = [e1]
        assert audit_log.verify_chain(db, wid) is False

    def test_tampered_payload_detected(self) -> None:
        wid = _make_workspace_id()
        e1 = _fake_event(wid, prev_hash="genesis")
        # tamper: change the action but leave hash unchanged
        e1.action = "evil.action"

        db = MagicMock()
        db.exec.return_value.all.return_value = [e1]
        assert audit_log.verify_chain(db, wid) is False

    def test_broken_chain_link_detected(self) -> None:
        wid = _make_workspace_id()
        e1 = _fake_event(wid, prev_hash="genesis")
        # e2 references a wrong prev_hash
        e2 = _fake_event(wid, prev_hash="wrong_prev")

        db = MagicMock()
        db.exec.return_value.all.return_value = [e1, e2]
        # e2 hash was computed with "wrong_prev" so its own hash is self-consistent,
        # but verify_chain recomputes using the running prev_hash (e1.hash) - should fail
        assert audit_log.verify_chain(db, wid) is False
