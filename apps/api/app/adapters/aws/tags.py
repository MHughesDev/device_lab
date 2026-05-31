"""
EC2 tagging conventions — patterns ported from cloud-custodian c7n/tags.py.
DeviceLab uses a DeviceLab: namespace on every managed resource.
"""

MANAGED_BY_TAG = "DeviceLab:ManagedBy"
MANAGED_BY_VALUE = "devicelab"


def device_tags(
    workspace_id: str,
    device_id: str,
    template_name: str,
    extra: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    tags: dict[str, str] = {
        MANAGED_BY_TAG: MANAGED_BY_VALUE,
        "DeviceLab:Workspace": workspace_id,
        "DeviceLab:Device": device_id,
        "DeviceLab:Template": template_name,
    }
    if extra:
        tags.update(extra)
    return [{"Key": k, "Value": v} for k, v in tags.items()]


def is_devicelab_managed(resource_tags: list[dict[str, str]]) -> bool:
    tag_map = {t["Key"]: t["Value"] for t in resource_tags}
    return tag_map.get(MANAGED_BY_TAG) == MANAGED_BY_VALUE


def find_orphaned_instances(ec2_client, workspace_id: str) -> list[str]:
    """Return instance IDs tagged with a workspace but not in known device IDs."""
    resp = ec2_client.describe_instances(
        Filters=[
            {"Name": f"tag:{MANAGED_BY_TAG}", "Values": [MANAGED_BY_VALUE]},
            {"Name": "tag:DeviceLab:Workspace", "Values": [workspace_id]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
        ]
    )
    result = []
    for reservation in resp.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            result.append(instance["InstanceId"])
    return result
