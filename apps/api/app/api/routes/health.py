from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text
from sqlmodel import Session

from app.api.deps import SessionDep
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check(db: SessionDep) -> dict:
    db_ok = True
    try:
        db.exec(text("SELECT 1"))  # type: ignore[call-overload]
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "db_ok": db_ok,
        "version": settings.VERSION if hasattr(settings, "VERSION") else "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }
