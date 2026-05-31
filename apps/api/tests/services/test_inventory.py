import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.models import Device, Workspace


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


def _fake_boto(instances=None, volumes=None):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {"Reservations": instances or []}
    mock_ec2.describe_volumes.return_value = {"Volumes": volumes or []}
    mock_ec2.terminate_instances = MagicMock()
    mock_ec2.delete_volume = MagicMock()
    mock_ec2.delete_snapshot = MagicMock()
    mock_boto = MagicMock()
    mock_boto.client.return_value = mock_ec2
    return mock_boto, mock_ec2


def test_list_tagged_resources_empty():
    from app.services.cost.inventory import list_tagged_resources
    mock_boto, _ = _fake_boto()
    result = list_tagged_resources(uuid.uuid4(), "us-east-1", boto_session=mock_boto)
    assert result == []


def test_detect_orphans_none():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        instance_id = "i-123"
        device = Device(
            workspace_id=ws.id,
            family="linux",
            state="ready",
            provider_ids_json=f'{{"instance_id": "{instance_id}", "region": "us-east-1"}}',
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(device)
        db.commit()

        instances = [{"Instances": [{"InstanceId": instance_id, "Tags": [], "InstanceType": "t3.micro"}]}]
        mock_boto, _ = _fake_boto(instances=instances)
        from app.services.cost.inventory import detect_orphans
        orphans = detect_orphans(db, ws.id, "us-east-1", boto_session=mock_boto)
    assert orphans == []


def test_detect_orphans_finds_untracked():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        instances = [{"Instances": [{"InstanceId": "i-untracked", "Tags": [], "InstanceType": "t3.micro"}]}]
        mock_boto, _ = _fake_boto(instances=instances)
        from app.services.cost.inventory import detect_orphans
        orphans = detect_orphans(db, ws.id, "us-east-1", boto_session=mock_boto)
    assert len(orphans) == 1
    assert orphans[0].provider_resource_id == "i-untracked"


def test_cleanup_orphan_terminates_instance():
    mock_boto, mock_ec2 = _fake_boto()
    from app.services.cost.inventory import cleanup_orphan
    cleanup_orphan("i-abc", "ec2_instance", "us-east-1", boto_session=mock_boto)
    mock_ec2.terminate_instances.assert_called_once_with(InstanceIds=["i-abc"])


def test_cleanup_orphan_unknown_type_raises():
    from app.services.cost.inventory import cleanup_orphan
    with pytest.raises(ValueError):
        cleanup_orphan("r-123", "unknown_type", "us-east-1", boto_session=MagicMock())
