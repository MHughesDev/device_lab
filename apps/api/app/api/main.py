from fastapi import APIRouter

from app.api.routes import cloud_accounts, devices, health, login, private, recipes, secrets, stream, templates, users, utils, workspace
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(health.router)
api_router.include_router(workspace.router)
api_router.include_router(cloud_accounts.router)
api_router.include_router(templates.router)
api_router.include_router(devices.router)
api_router.include_router(secrets.router)
api_router.include_router(recipes.router)
api_router.include_router(stream.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
