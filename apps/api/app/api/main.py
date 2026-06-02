from fastapi import APIRouter

from app.api.routes import cloud_accounts, cost, device_logs, devices, health, host, login, manifests, private, recipes, replay, secrets, snapshots, stream, templates, test_runs, users, utils, workspace
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
api_router.include_router(device_logs.router)
api_router.include_router(secrets.router)
api_router.include_router(recipes.router)
api_router.include_router(stream.router)
api_router.include_router(stream.display_router)
api_router.include_router(manifests.router)
api_router.include_router(cost.router)
api_router.include_router(snapshots.router)
api_router.include_router(test_runs.router)
api_router.include_router(replay.router)
api_router.include_router(host.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
