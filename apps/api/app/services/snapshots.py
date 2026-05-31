# snapshots.py — Snapshot service: create, poll, fork, and delete device snapshots
from __future__ import annotations
import json
import uuid
from datetime import UTC, datetime, timedelta
from sqlmodel import Session
from app.models import Device, Snapshot

SNAPSHOT_CAPABLE_FAMILIES = {"linux"}


class CapabilityUnsupportedError(Exception):
    def __init__(self, capability: str, family: str):
        self.capability = capability
        self.family = family
        super().__init__(f"CAPABILITY_UNSUPPORTED: {capability} not available for family {family}")


async def create_snapshot(
    db: Session,
    workspace_id: uuid.UUID,
    device_id: uuid.UUID,
    boto_session=None,
) -> Snapshot:
    """Initiate an EBS snapshot for a Linux device. Returns Snapshot in 'pending' status."""
    device = db.get(Device, device_id)
    if not device:
        raise ValueError(f"Device {device_id} not found")
    if device.family not in SNAPSHOT_CAPABLE_FAMILIES:
        raise CapabilityUnsupportedError("snapshot", device.family)

    provider_ids = json.loads(device.provider_ids_json or "{}")
    instance_id = provider_ids.get("instance_id", "")
    region = provider_ids.get("region", "us-east-1")

    from app.adapters.linux.snapshots import get_root_volume_id, create_ebs_snapshot
    volume_id = get_root_volume_id(instance_id, region, boto_session)
    tags = {
        "DeviceLab:Workspace": str(workspace_id),
        "DeviceLab:Device": str(device_id),
    }
    provider_snapshot_id = create_ebs_snapshot(volume_id, region, tags, boto_session)

    snap = Snapshot(
        workspace_id=workspace_id,
        source_device_id=device_id,
        status="pending",
        provider_snapshot_id=provider_snapshot_id,
        family=device.family,
        region=region,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


async def poll_snapshot_status(
    db: Session,
    snapshot_id: uuid.UUID,
    boto_session=None,
) -> Snapshot:
    """Check EBS snapshot state and update DB record."""
    snap = db.get(Snapshot, snapshot_id)
    if not snap or not snap.provider_snapshot_id:
        raise ValueError(f"Snapshot {snapshot_id} not found or has no provider ID")

    from app.adapters.linux.snapshots import describe_ebs_snapshot
    info = describe_ebs_snapshot(snap.provider_snapshot_id, snap.region, boto_session)

    raw_status = info["status"]
    if raw_status == "completed":
        snap.status = "complete"
        snap.size_gb = float(info.get("volume_size", 0))
        snap.completed_at = datetime.now(UTC)
    elif raw_status == "error":
        snap.status = "failed"

    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


async def fork_from_snapshot(
    db: Session,
    snapshot_id: uuid.UUID,
    workspace_id: uuid.UUID,
    template_overrides: dict,
    boto_session=None,
) -> Device:
    """Launch a new EC2 instance from a snapshot. Returns Device in 'provisioning' state."""
    snap = db.get(Snapshot, snapshot_id)
    if not snap:
        raise ValueError(f"Snapshot {snapshot_id} not found")

    import boto3
    session = boto_session or boto3
    ec2 = session.client("ec2", region_name=snap.region)

    instance_type = template_overrides.get("instance_type", "t3.micro")
    resp = ec2.run_instances(
        ImageId=template_overrides.get("ami_id", "ami-placeholder"),
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/xvda",
                "Ebs": {"SnapshotId": snap.provider_snapshot_id},
            }
        ],
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "DeviceLab:Workspace", "Value": str(workspace_id)},
                    {"Key": "DeviceLab:ForkedFrom", "Value": str(snapshot_id)},
                ],
            }
        ],
    )
    instance_id = resp["Instances"][0]["InstanceId"]

    device = Device(
        workspace_id=workspace_id,
        family=snap.family,
        state="provisioning",
        provider_ids_json=json.dumps({"instance_id": instance_id, "region": snap.region}),
        tags_json=json.dumps({"forked_from": str(snapshot_id)}),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


async def delete_snapshot(
    db: Session,
    snapshot_id: uuid.UUID,
    workspace_id: uuid.UUID,
    boto_session=None,
    dangerous_mode: bool = False,
) -> None:
    """Delete an EBS snapshot. Raises ValueError for snapshots < 24h old unless dangerous_mode."""
    snap = db.get(Snapshot, snapshot_id)
    if not snap:
        raise ValueError(f"Snapshot {snapshot_id} not found")

    age = datetime.now(UTC) - snap.created_at.replace(tzinfo=UTC) if snap.created_at.tzinfo is None else datetime.now(UTC) - snap.created_at
    if age < timedelta(hours=24) and not dangerous_mode:
        raise ValueError("Cannot delete snapshot less than 24h old without dangerous_mode")

    from app.adapters.linux.snapshots import delete_ebs_snapshot
    if snap.provider_snapshot_id:
        delete_ebs_snapshot(snap.provider_snapshot_id, snap.region, boto_session)

    snap.status = "deleted"
    db.add(snap)
    db.commit()
