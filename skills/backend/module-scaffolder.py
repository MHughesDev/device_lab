# skills/backend/module-scaffolder.py
"""Create a bounded-context skeleton under apps/api/app/<module>/ (full pattern)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def _title_case_snake(name: str) -> str:
    return name.replace("_", " ").title().replace(" ", "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold FastAPI bounded context module")
    parser.add_argument("--module", required=True, help="snake_case module name, e.g. billing")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    name = args.module.strip().lower()
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        print("Invalid module name — use snake_case [a-z][a-z0-9_]*", file=sys.stderr)
        return 1
    if name == "example":
        print("Refusing to overwrite the teaching module `example`.", file=sys.stderr)
        return 1

    title = _title_case_snake(name)
    base = args.repo_root / "apps" / "api" / "src" / name
    if base.exists():
        print(f"Already exists: {base}", file=sys.stderr)
        return 1
    base.mkdir(parents=True)

    files: dict[str, str] = {}

    files[f"apps/api/app/{name}/__init__.py"] = f'''# apps/api/app/{name}/__init__.py
"""Bounded context: {name}."""

from apps.api.src.{name}.router import router

__all__ = ["router"]
'''

    files[f"apps/api/app/{name}/models.py"] = f'''# apps/api/app/{name}/models.py
"""SQLAlchemy models for {name}."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.src.database import Base


class {title}Entity(Base):
    """Placeholder entity — replace with your domain model."""

    __tablename__ = "{name}_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
'''

    files[f"apps/api/app/{name}/schemas.py"] = f'''# apps/api/app/{name}/schemas.py
"""Pydantic schemas for {name}."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class {title}Create(BaseModel):
    """Create payload."""

    name: str = Field(..., min_length=1, max_length=255)


class {title}Response(BaseModel):
    """Single resource response."""

    model_config = {{"from_attributes": True}}

    id: uuid.UUID
    name: str
    created_at: datetime
'''

    files[f"apps/api/app/{name}/repository.py"] = f'''# apps/api/app/{name}/repository.py
"""Persistence layer for {name}."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.{name}.models import {title}Entity


class {title}Repository:
    """Database access for {name}."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> {title}Entity | None:
        return await self._session.get({title}Entity, entity_id)

    async def list_all(self) -> list[{title}Entity]:
        result = await self._session.execute(select({title}Entity))
        return list(result.scalars().all())

    async def create(self, row: {title}Entity) -> {title}Entity:
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row
'''

    files[f"apps/api/app/{name}/service.py"] = f'''# apps/api/app/{name}/service.py
"""Application service for {name}."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from apps.api.src.{name}.models import {title}Entity
from apps.api.src.{name}.repository import {title}Repository
from apps.api.src.{name}.schemas import {title}Create, {title}Response
from apps.api.src.exceptions import NotFoundError


class {title}Service:
    """Domain operations for {name}."""

    def __init__(self, repo: {title}Repository) -> None:
        self._repo = repo

    async def get(self, entity_id: uuid.UUID) -> {title}Entity:
        row = await self._repo.get_by_id(entity_id)
        if row is None:
            raise NotFoundError("{title}Entity", str(entity_id))
        return row

    async def create(self, data: {title}Create) -> {title}Entity:
        now = datetime.now(UTC)
        row = {title}Entity(name=data.name, created_at=now)
        return await self._repo.create(row)

    async def list_all(self) -> list[{title}Response]:
        rows = await self._repo.list_all()
        return [self.to_response(r) for r in rows]

    def to_response(self, row: {title}Entity) -> {title}Response:
        return {title}Response.model_validate(row)
'''

    files[f"apps/api/app/{name}/dependencies.py"] = f'''# apps/api/app/{name}/dependencies.py
"""FastAPI dependencies for {name}."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.database import get_db
from apps.api.src.{name}.repository import {title}Repository
from apps.api.src.{name}.service import {title}Service


def get_{name}_service(
    session: AsyncSession = Depends(get_db),
) -> {title}Service:
    """Wire repository into service."""

    return {title}Service(repo={title}Repository(session))
'''

    files[f"apps/api/app/{name}/router.py"] = f'''# apps/api/app/{name}/router.py
"""HTTP routes for {name}."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.src.auth.dependencies import app_error_to_http, get_current_user
from apps.api.src.auth.models import User
from apps.api.src.{name}.dependencies import get_{name}_service
from apps.api.src.{name}.schemas import {title}Create, {title}Response
from apps.api.src.{name}.service import {title}Service
from apps.api.src.exceptions import AppError

router = APIRouter(prefix="/{name}", tags=["{title}"])


def _handle(exc: AppError) -> HTTPException:
    return app_error_to_http(exc)


@router.get("/", response_model=list[{title}Response])
async def list_{name}(
    service: {title}Service = Depends(get_{name}_service),
    _user: User = Depends(get_current_user),
) -> list[{title}Response]:
    try:
        return await service.list_all()
    except AppError as exc:
        raise _handle(exc) from exc


@router.post("/", response_model={title}Response, status_code=status.HTTP_201_CREATED)
async def create_{name}(
    body: {title}Create,
    service: {title}Service = Depends(get_{name}_service),
    _user: User = Depends(get_current_user),
) -> {title}Response:
    try:
        row = await service.create(body)
        return service.to_response(row)
    except AppError as exc:
        raise _handle(exc) from exc


@router.get("/{{entity_id}}", response_model={title}Response)
async def get_{name}(
    entity_id: uuid.UUID,
    service: {title}Service = Depends(get_{name}_service),
    _user: User = Depends(get_current_user),
) -> {title}Response:
    try:
        row = await service.get(entity_id)
        return service.to_response(row)
    except AppError as exc:
        raise _handle(exc) from exc
'''

    created: list[str] = []
    for rel, content in files.items():
        path = args.repo_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(rel)

    for rel in sorted(created):
        print(f"Created {rel}")
    print()
    print("Next steps:")
    print("  1. Register router in apps/api/app/main.py")
    print("  2. Import models in apps/api/alembic/env.py and add Alembic migration")
    print("  3. Run: make migrate && make test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
