import json
import uuid

from sqlmodel import Session, select

from app.models import DeviceTemplate

SEED_TEMPLATES = [
    {
        "id": "00000000-0000-0000-0001-000000000001",
        "family": "linux",
        "name": "linux-default",
        "description": "Ubuntu 24.04 LTS on t3.medium. SSM-managed. No inbound ports.",
        "capability_json": json.dumps({
            "observe": ["ax_tree", "screenshot", "ocr"],
            "interact": ["keyboard", "mouse", "shell"],
            "streaming": False,
        }),
        "supported_regions": json.dumps([
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-northeast-1",
        ]),
    },
]


def ensure_seed_templates(db: Session) -> None:
    for t in SEED_TEMPLATES:
        tid = uuid.UUID(t["id"])
        existing = db.get(DeviceTemplate, tid)
        if not existing:
            db.add(DeviceTemplate(
                id=tid,
                family=t["family"],
                name=t["name"],
                description=t["description"],
                capability_json=t["capability_json"],
                supported_regions=t["supported_regions"],
            ))
    db.commit()


def list_templates(db: Session) -> list[DeviceTemplate]:
    return list(db.exec(select(DeviceTemplate)).all())


def list_local_templates(db: Session) -> list[DeviceTemplate]:
    """Return only templates whose family can run locally on the current host.

    Cloud templates are never excluded — this filter applies only to the
    local-placement subset. Families the host cannot support locally are
    removed from the result.
    """
    from app.services.local.host_probe import probe_host
    from app.services.local.placement import _host_can_run_local

    caps = probe_host()
    all_templates = list_templates(db)
    return [t for t in all_templates if _host_can_run_local(t.family, caps)]
