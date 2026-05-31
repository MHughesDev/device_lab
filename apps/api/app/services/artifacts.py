# artifacts.py — Artifact store service: persist metadata, generate presigned URLs, purge expired
from __future__ import annotations
import uuid
from datetime import UTC, datetime, timedelta
from sqlmodel import Session, select
from app.models import Artifact


def store_artifact(
    db: Session,
    workspace_id: uuid.UUID,
    artifact_type: str,
    storage_path: str,
    content_type: str,
    size_bytes: int,
    run_id: uuid.UUID | None = None,
    evidence_id: uuid.UUID | None = None,
    session_id: str | None = None,
    retention_days: int = 30,
) -> Artifact:
    """Persist artifact metadata. Does NOT upload — caller handles storage."""
    purge_after = datetime.now(UTC) + timedelta(days=retention_days)
    artifact = Artifact(
        workspace_id=workspace_id,
        artifact_type=artifact_type,
        storage_path=storage_path,
        content_type=content_type,
        size_bytes=size_bytes,
        run_id=run_id,
        evidence_id=evidence_id,
        session_id=session_id,
        retention_days=retention_days,
        purge_after=purge_after,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def get_presigned_download_url(
    artifact: Artifact,
    expires_in_seconds: int = 3600,
    boto_session=None,
) -> str:
    """Generate a presigned GET URL for an S3-stored artifact. Returns path for local dev."""
    path = artifact.storage_path
    if not path.startswith("s3://"):
        return path
    # Parse s3://bucket/key
    without_scheme = path[len("s3://"):]
    bucket, _, key = without_scheme.partition("/")
    import boto3
    session = boto_session or boto3
    s3 = session.client("s3")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in_seconds,
    )


def list_artifacts(
    db: Session,
    workspace_id: uuid.UUID,
    run_id: uuid.UUID | None = None,
    evidence_id: uuid.UUID | None = None,
) -> list[Artifact]:
    """Return artifacts matching filters, excluding purged=True rows."""
    stmt = select(Artifact).where(
        Artifact.workspace_id == workspace_id,
        Artifact.purged == False,  # noqa: E712
    )
    if run_id is not None:
        stmt = stmt.where(Artifact.run_id == run_id)
    if evidence_id is not None:
        stmt = stmt.where(Artifact.evidence_id == evidence_id)
    return list(db.exec(stmt).all())


def purge_expired(db: Session, workspace_id: uuid.UUID) -> int:
    """Mark all artifacts past their purge_after date as purged=True. Returns count."""
    now = datetime.now(UTC)
    stmt = select(Artifact).where(
        Artifact.workspace_id == workspace_id,
        Artifact.purged == False,  # noqa: E712
        Artifact.purge_after <= now,
    )
    rows = db.exec(stmt).all()
    for row in rows:
        row.purged = True
        db.add(row)
    db.commit()
    return len(rows)
