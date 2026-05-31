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
    {
        "id": "00000000-0000-0000-0002-000000000001",
        "family": "browser",
        "name": "browser-local",
        "description": "Local Chromium browser session via Playwright. No cloud account required.",
        "capability_json": json.dumps({
            "observe": ["ax_tree", "screenshot"],
            "interact": ["click", "type", "navigate", "fill_form"],
            "streaming": False,
        }),
        "supported_regions": json.dumps([]),
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
