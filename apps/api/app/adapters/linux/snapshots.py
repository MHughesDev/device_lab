# snapshots.py — Linux EBS snapshot adapter: create, describe, delete EBS snapshots via boto3
from __future__ import annotations


def get_root_volume_id(instance_id: str, region: str, boto_session=None) -> str:
    """Describe EC2 instance and return the root EBS volume ID."""
    import boto3

    session = boto_session or boto3
    ec2 = session.client("ec2", region_name=region)
    resp = ec2.describe_instances(InstanceIds=[instance_id])
    reservations = resp.get("Reservations", [])
    if not reservations:
        raise ValueError(f"Instance {instance_id} not found")
    for bdm in reservations[0]["Instances"][0].get("BlockDeviceMappings", []):
        if bdm.get("DeviceName") in ("/dev/xvda", "/dev/sda1"):
            return bdm["Ebs"]["VolumeId"]
    raise ValueError(f"No root volume found for instance {instance_id}")


def create_ebs_snapshot(
    volume_id: str,
    region: str,
    tags: dict[str, str],
    boto_session=None,
) -> str:
    """Call ec2.create_snapshot and return the SnapshotId string."""
    import boto3

    session = boto_session or boto3
    ec2 = session.client("ec2", region_name=region)
    tag_specs = [{"ResourceType": "snapshot", "Tags": [{"Key": k, "Value": v} for k, v in tags.items()]}]
    resp = ec2.create_snapshot(VolumeId=volume_id, TagSpecifications=tag_specs)
    return resp["SnapshotId"]


def describe_ebs_snapshot(snapshot_id: str, region: str, boto_session=None) -> dict:
    """Return dict with keys: status, volume_size, start_time."""
    import boto3

    session = boto_session or boto3
    ec2 = session.client("ec2", region_name=region)
    resp = ec2.describe_snapshots(SnapshotIds=[snapshot_id])
    snap = resp["Snapshots"][0]
    raw_state = snap.get("State", "pending")
    status_map = {"pending": "pending", "completed": "completed", "error": "error"}
    return {
        "status": status_map.get(raw_state, raw_state),
        "volume_size": snap.get("VolumeSize", 0),
        "start_time": snap.get("StartTime"),
    }


def delete_ebs_snapshot(snapshot_id: str, region: str, boto_session=None) -> None:
    """Call ec2.delete_snapshot."""
    import boto3

    session = boto_session or boto3
    ec2 = session.client("ec2", region_name=region)
    ec2.delete_snapshot(SnapshotId=snapshot_id)
