# inventory.py — CloudInventory: tag-based resource listing and orphan detection
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlmodel import Session, select
from app.models import Device, OrphanResource
from app.services.cost.pricing import estimate_monthly_cost

DEVICELAB_TAG_KEY = "DeviceLab:Workspace"


def list_tagged_resources(workspace_id: uuid.UUID, region: str, boto_session=None) -> list[dict]:
    """Return all EC2 instances + EBS volumes tagged DeviceLab:Workspace={workspace_id}."""
    import boto3

    session = boto_session or boto3
    ec2 = session.client("ec2", region_name=region)
    tag_filter = [{"Name": f"tag:{DEVICELAB_TAG_KEY}", "Values": [str(workspace_id)]}]

    resources: list[dict] = []

    reservations = ec2.describe_instances(Filters=tag_filter).get("Reservations", [])
    for res in reservations:
        for inst in res.get("Instances", []):
            tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
            resources.append({
                "resource_id": inst["InstanceId"],
                "resource_type": "ec2_instance",
                "tags": tags,
                "region": region,
                "instance_type": inst.get("InstanceType", ""),
            })

    volumes = ec2.describe_volumes(Filters=tag_filter).get("Volumes", [])
    for vol in volumes:
        tags = {t["Key"]: t["Value"] for t in vol.get("Tags", [])}
        resources.append({
            "resource_id": vol["VolumeId"],
            "resource_type": "ebs_volume",
            "tags": tags,
            "region": region,
            "size_gb": vol.get("Size", 0),
        })

    return resources


def detect_orphans(
    db: Session,
    workspace_id: uuid.UUID,
    region: str,
    boto_session=None,
) -> list[OrphanResource]:
    """Compare tagged AWS resources against Device table. Missing from DB = orphan."""
    resources = list_tagged_resources(workspace_id, region, boto_session)

    known_devices = db.exec(select(Device)).all()
    known_ids: set[str] = set()
    for d in known_devices:
        if d.provider_ids_json:
            import json as _json
            try:
                ids = _json.loads(d.provider_ids_json)
                if "instance_id" in ids:
                    known_ids.add(ids["instance_id"])
                if "volume_id" in ids:
                    known_ids.add(ids["volume_id"])
            except Exception:
                pass

    orphans: list[OrphanResource] = []
    for r in resources:
        if r["resource_id"] not in known_ids:
            if r["resource_type"] == "ec2_instance":
                monthly = str(estimate_monthly_cost(region, r.get("instance_type", "t3.micro")))
            else:
                size_gb = r.get("size_gb", 0)
                monthly = str((0.1 * size_gb).__round__(2))
            orphans.append(OrphanResource(
                provider_resource_id=r["resource_id"],
                resource_type=r["resource_type"],
                region=region,
                tags=r["tags"],
                estimated_monthly_cost_usd=monthly,
                last_seen_at=datetime.now(UTC),
            ))

    orphans.sort(key=lambda o: float(o.estimated_monthly_cost_usd), reverse=True)
    return orphans


def cleanup_orphan(resource_id: str, resource_type: str, region: str, boto_session=None) -> None:
    """Terminate/delete a single orphan resource. Caller must confirm dangerous_mode first."""
    import boto3

    session = boto_session or boto3
    ec2 = session.client("ec2", region_name=region)

    if resource_type == "ec2_instance":
        ec2.terminate_instances(InstanceIds=[resource_id])
    elif resource_type == "ebs_volume":
        ec2.delete_volume(VolumeId=resource_id)
    elif resource_type == "ebs_snapshot":
        ec2.delete_snapshot(SnapshotId=resource_id)
    else:
        raise ValueError(f"Unsupported resource_type: {resource_type}")
