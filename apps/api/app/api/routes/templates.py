from fastapi import APIRouter

from app.api.deps import SessionDep
from app.models import DeviceTemplatePublic
from app.services.templates import ensure_seed_templates, list_templates

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/", response_model=list[DeviceTemplatePublic])
def get_templates(db: SessionDep) -> list[DeviceTemplatePublic]:
    ensure_seed_templates(db)
    templates = list_templates(db)
    return [
        DeviceTemplatePublic(
            id=t.id,
            family=t.family,
            name=t.name,
            description=t.description,
            capability_json=t.capability_json,
            supported_regions=t.supported_regions,
        )
        for t in templates
    ]
