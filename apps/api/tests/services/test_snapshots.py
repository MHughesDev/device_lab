import json
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.models import Device, Snapshot, Workspace


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


def _make_device(db, workspace_id, family="linux"):
    device = Device(
        workspace_id=workspace_id,
        family=family,
        state="ready",
        provider_ids_json=json.dumps({"instance_id": "i-abc", "region": "us-east-1"}),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.mark.asyncio
async def test_create_snapshot_browser_raises():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id, family="browser")
        from app.services.snapshots import create_snapshot, CapabilityUnsupportedError
        with pytest.raises(CapabilityUnsupportedError):
            await create_snapshot(db, ws.id, device.id)


@pytest.mark.asyncio
async def test_create_snapshot_linux_pending():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        device = _make_device(db, ws.id, family="linux")
        with (
            patch("app.adapters.linux.snapshots.get_root_volume_id", return_value="vol-123"),
            patch("app.adapters.linux.snapshots.create_ebs_snapshot", return_value="snap-456"),
        ):
            from app.services.snapshots import create_snapshot
            snap = await create_snapshot(db, ws.id, device.id)
    assert snap.status == "pending"
    assert snap.provider_snapshot_id == "snap-456"


@pytest.mark.asyncio
async def test_poll_snapshot_status_completes():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        snap = Snapshot(
            workspace_id=ws.id,
            source_device_id=uuid.uuid4(),
            provider_snapshot_id="snap-789",
            family="linux",
            region="us-east-1",
            created_at=datetime.now(UTC),
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)

        with patch(
            "app.adapters.linux.snapshots.describe_ebs_snapshot",
            return_value={"status": "completed", "volume_size": 20, "start_time": datetime.now(UTC)},
        ):
            from app.services.snapshots import poll_snapshot_status
            updated = await poll_snapshot_status(db, snap.id)
    assert updated.status == "complete"
    assert updated.size_gb == 20.0


@pytest.mark.asyncio
async def test_delete_snapshot_young_requires_dangerous():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        snap = Snapshot(
            workspace_id=ws.id,
            source_device_id=uuid.uuid4(),
            provider_snapshot_id="snap-young",
            family="linux",
            region="us-east-1",
            created_at=datetime.now(UTC),
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)

        from app.services.snapshots import delete_snapshot
        with pytest.raises(ValueError, match="24h"):
            await delete_snapshot(db, snap.id, ws.id, dangerous_mode=False)


@pytest.mark.asyncio
async def test_fork_creates_device():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        snap = Snapshot(
            workspace_id=ws.id,
            source_device_id=uuid.uuid4(),
            provider_snapshot_id="snap-fork",
            family="linux",
            region="us-east-1",
            created_at=datetime.now(UTC),
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)

        mock_boto = MagicMock()
        mock_boto.client.return_value.run_instances.return_value = {
            "Instances": [{"InstanceId": "i-forked"}]
        }
        from app.services.snapshots import fork_from_snapshot
        device = await fork_from_snapshot(db, snap.id, ws.id, {}, boto_session=mock_boto)
    assert device.state == "provisioning"
