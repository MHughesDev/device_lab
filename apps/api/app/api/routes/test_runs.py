# test_runs.py — TestRun and Artifact API routes
import uuid

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import ArtifactPublic, TestRunCreate, TestRunPublic, Workspace
from app.services import artifacts as artifact_svc
from app.services import test_runs as test_run_svc

router = APIRouter(tags=["test_runs"])


def _get_workspace(db) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialised")
    return ws


@router.post("/test-runs", response_model=TestRunPublic, status_code=201)
async def create_test_run(
    body: TestRunCreate, db: SessionDep, current_user: CurrentUser
) -> object:
    ws = _get_workspace(db)
    return await test_run_svc.create_test_run(db, ws.id, body)


@router.get("/test-runs/{run_id}", response_model=TestRunPublic)
def get_test_run(run_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> object:
    run = test_run_svc.get_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="TestRun not found")
    return run


@router.get("/test-runs/{run_id}/artifacts", response_model=list[ArtifactPublic])
def list_test_run_artifacts(run_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> list:
    ws = _get_workspace(db)
    arts = artifact_svc.list_artifacts(db, ws.id, run_id=run_id)
    result = []
    for a in arts:
        pub = ArtifactPublic(
            id=a.id,
            artifact_type=a.artifact_type,
            content_type=a.content_type,
            size_bytes=a.size_bytes,
            captured_at=a.captured_at,
            purge_after=a.purge_after,
            download_url=artifact_svc.get_presigned_download_url(a),
        )
        result.append(pub)
    return result


@router.get("/test-runs/{run_id}/junit")
def get_junit_xml(run_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> PlainTextResponse:
    run = test_run_svc.get_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="TestRun not found")
    xml_str = test_run_svc.build_junit_xml(run)
    return PlainTextResponse(xml_str, media_type="application/xml")


@router.get("/artifacts/{artifact_id}", response_model=ArtifactPublic)
def get_artifact(artifact_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> ArtifactPublic:
    from app.models import Artifact
    artifact = db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ArtifactPublic(
        id=artifact.id,
        artifact_type=artifact.artifact_type,
        content_type=artifact.content_type,
        size_bytes=artifact.size_bytes,
        captured_at=artifact.captured_at,
        purge_after=artifact.purge_after,
        download_url=artifact_svc.get_presigned_download_url(artifact),
    )
