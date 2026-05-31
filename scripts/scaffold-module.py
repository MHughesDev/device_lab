# scripts/scaffold-module.py
"""Scaffold a bounded context under apps/api/app/<module>/ with tests and main.py wiring."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def _title_case_snake(name: str) -> str:
    return name.replace("_", " ").title().replace(" ", "")


_IMPORT_MARKER = "# SCAFFOLD: module imports — do not remove this line"
_INCLUDE_MARKER = "# SCAFFOLD: router includes — do not remove this line"


def _wire_main_py(repo_root: Path, name: str) -> None:
    main_py = repo_root / "apps" / "api" / "src" / "main.py"
    text = main_py.read_text(encoding="utf-8")
    import_line = f"from apps.api.src.{name}.router import router as {name}_router"
    include_line = f"    app.include_router({name}_router, prefix=resolved.api_prefix)"

    if import_line in text and include_line in text:
        print(f"main.py already wired for module: {name}")
        return

    # Insert import after SCAFFOLD_MARKER (preferred) or after example_router import (fallback)
    if _IMPORT_MARKER in text:
        text = text.replace(
            _IMPORT_MARKER + "\n",
            _IMPORT_MARKER + "\n" + import_line + "\n",
            1,
        )
    elif "from apps.api.src.example.router import router as example_router\n" in text:
        text = text.replace(
            "from apps.api.src.example.router import router as example_router\n",
            "from apps.api.src.example.router import router as example_router\n"
            + import_line + "\n",
            1,
        )
    else:
        raise RuntimeError(
            "Could not find SCAFFOLD_MARKER or fallback import anchor in main.py. "
            "Add '# SCAFFOLD: module imports — do not remove this line' before router imports."
        )

    # Insert router include after SCAFFOLD_MARKER (preferred) or after example_router include (fallback)
    if _INCLUDE_MARKER in text:
        text = text.replace(
            _INCLUDE_MARKER + "\n",
            _INCLUDE_MARKER + "\n" + include_line + "\n",
            1,
        )
    elif "    app.include_router(example_router, prefix=resolved.api_prefix)\n" in text:
        text = text.replace(
            "    app.include_router(example_router, prefix=resolved.api_prefix)\n",
            "    app.include_router(example_router, prefix=resolved.api_prefix)\n"
            + include_line + "\n",
            1,
        )
    else:
        raise RuntimeError(
            "Could not find SCAFFOLD_MARKER or fallback include anchor in main.py. "
            "Add '# SCAFFOLD: router includes — do not remove this line' before router includes."
        )

    main_py.write_text(text, encoding="utf-8")


def _validate_syntax(root: Path, name: str) -> list[str]:
    """Import each generated Python file to catch syntax errors immediately."""
    import subprocess as _sp

    module_dir = root / "apps" / "api" / "src" / name
    py_files = list(module_dir.rglob("*.py"))
    failures: list[str] = []
    for f in py_files:
        result = _sp.run(  # noqa: S603 — path is under repo-generated module_dir only
            [sys.executable, "-c", f"import ast; ast.parse(open({str(f)!r}).read())"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"{f.relative_to(root)}: {result.stderr.strip()}")
    return failures


def _auto_migrate(root: Path, name: str) -> bool:
    """Run alembic revision --autogenerate for the new module. Returns True on success."""
    import subprocess as _sp

    api_dir = root / "apps" / "api"
    result = _sp.run(  # noqa: S603 — alembic invoked with fixed args under repo apps/api
        [
            sys.executable,
            "-m",
            "alembic",
            "revision",
            "--autogenerate",
            "-m",
            f"add_{name}_table",
        ],
        cwd=str(api_dir),
        capture_output=False,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold bounded context module")
    parser.add_argument("--module", required=True, help="snake_case module name")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--auto-migrate",
        action="store_true",
        help="Run alembic revision --autogenerate after scaffolding",
    )
    args = parser.parse_args()
    name = args.module.strip().lower()
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        print("Invalid module name — use snake_case [a-z][a-z0-9_]*", file=sys.stderr)
        return 1
    if name == "example":
        print("Refusing to overwrite the teaching module `example`.", file=sys.stderr)
        return 1

    title = _title_case_snake(name)
    root = args.repo_root
    base = root / "apps" / "api" / "src" / name
    if base.exists():
        print(f"Already exists: {base}", file=sys.stderr)
        return 1
    base.mkdir(parents=True)
    tests = base / "tests"
    tests.mkdir()

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


class {title}Record(Base):
    """Stub entity for {name} bounded context."""

    __tablename__ = "{name}_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
'''

    files[f"apps/api/app/{name}/schemas.py"] = f'''# apps/api/app/{name}/schemas.py
"""Pydantic schemas for {name}."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class {title}Base(BaseModel):
    """Shared fields."""

    label: str = Field(default="", max_length=255)


class {title}Create(BaseModel):
    """Create payload."""

    label: str = Field(..., min_length=1, max_length=255)


class {title}Update(BaseModel):
    """Update payload."""

    label: str | None = Field(default=None, min_length=1, max_length=255)


class {title}Response(BaseModel):
    """API response."""

    model_config = {{"from_attributes": True}}

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    label: str
'''

    files[
        f"apps/api/app/{name}/repository.py"
    ] = f'''# apps/api/app/{name}/repository.py
"""Persistence layer for {name}."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.{name}.models import {title}Record


class {title}Repository:
    """Database access for {name}."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, record_id: uuid.UUID) -> {title}Record | None:
        return await self._session.get({title}Record, record_id)

    async def list_all(self) -> list[{title}Record]:
        result = await self._session.execute(select({title}Record))
        return list(result.scalars().all())

    async def create(self, row: {title}Record) -> {title}Record:
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

from apps.api.src.{name}.models import {title}Record
from apps.api.src.{name}.repository import {title}Repository
from apps.api.src.{name}.schemas import {title}Create, {title}Response
from apps.api.src.exceptions import NotFoundError


class {title}Service:
    """Domain operations for {name}."""

    def __init__(self, repo: {title}Repository) -> None:
        self._repo = repo

    async def get(self, record_id: uuid.UUID) -> {title}Record:
        row = await self._repo.get_by_id(record_id)
        if row is None:
            raise NotFoundError("{title}Record", str(record_id))
        return row

    async def create(self, data: {title}Create) -> {title}Record:
        now = datetime.now(UTC)
        row = {title}Record(
            label=data.label,
            created_at=now,
            updated_at=now,
        )
        return await self._repo.create(row)

    async def list_all(self) -> list[{title}Response]:
        rows = await self._repo.list_all()
        return [self.to_response(r) for r in rows]

    def to_response(self, row: {title}Record) -> {title}Response:
        return {title}Response(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            label=row.label,
        )
'''

    files[
        f"apps/api/app/{name}/dependencies.py"
    ] = f'''# apps/api/app/{name}/dependencies.py
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

router = APIRouter(prefix="/{name}", tags=["{name}"])


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


@router.get("/{{record_id}}", response_model={title}Response)
async def get_{name}(
    record_id: uuid.UUID,
    service: {title}Service = Depends(get_{name}_service),
    _user: User = Depends(get_current_user),
) -> {title}Response:
    try:
        row = await service.get(record_id)
        return service.to_response(row)
    except AppError as exc:
        raise _handle(exc) from exc
'''

    files[f"apps/api/app/{name}/tests/__init__.py"] = (
        f"# apps/api/app/{name}/tests/__init__.py\n"
    )

    files[
        f"apps/api/app/{name}/tests/conftest.py"
    ] = f'''# apps/api/app/{name}/tests/conftest.py
"""Module-local pytest fixtures for {name}."""

from __future__ import annotations

# Add fixtures shared only by this bounded context's tests.
'''

    files[
        f"apps/api/app/{name}/tests/test_router.py"
    ] = f'''# apps/api/app/{name}/tests/test_router.py
"""HTTP tests for {name} router (stubs)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_{name}_happy_path_stub(client: AsyncClient) -> None:
    """Placeholder: authenticate and call list endpoint."""

    assert client is not None


@pytest.mark.asyncio
async def test_list_{name}_returns_401_without_auth(client: AsyncClient) -> None:
    """Placeholder: unauthenticated request should yield 401."""

    response = await client.get("/api/v1/{name}/")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_{name}_returns_404_unknown_id(client: AsyncClient) -> None:
    """Placeholder: missing resource returns 404 when authenticated."""

    rid = uuid.uuid4()
    response = await client.get(f"/api/v1/{name}/{{rid}}")
    assert response.status_code in (401, 403, 404)
'''

    files[
        f"apps/api/app/{name}/tests/test_service.py"
    ] = f'''# apps/api/app/{name}/tests/test_service.py
"""Unit tests for {title}Service (stubs)."""

from __future__ import annotations

from apps.api.src.{name}.service import {title}Service


def test_service_stub_instantiation() -> None:
    """Placeholder core service test."""

    assert {title}Service.__name__ == "{title}Service"
'''

    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Created {rel}")

    _wire_main_py(root, name)

    # Register models for Alembic/tests metadata
    conftest = root / "apps" / "api" / "tests" / "conftest.py"
    if conftest.is_file():
        ct = conftest.read_text(encoding="utf-8")
        import_line = (
            f"from apps.api.src.{name} import models as {name}_models  # noqa: F401\n"
        )
        anchor = (
            "from apps.api.src.example import models as example_models  # noqa: F401\n"
        )
        if anchor in ct and import_line not in ct:
            ct = ct.replace(anchor, anchor + import_line, 1)
            conftest.write_text(ct, encoding="utf-8")
            print(f"Updated apps/api/tests/conftest.py — import {name} models")

    # Syntax validation — catch codegen errors immediately
    syntax_errors = _validate_syntax(root, name)
    if syntax_errors:
        print("\nSyntax errors in generated files:", file=sys.stderr)
        for err in syntax_errors:
            print(f"  ✗ {err}", file=sys.stderr)
        return 1
    print("✓ Syntax validation passed for all generated files")

    if args.auto_migrate:
        print(f"\nRunning alembic autogenerate for {name}...")
        if _auto_migrate(root, name):
            print("✓ Migration generated — review it before applying")
        else:
            print("⚠ Migration generation failed — run manually: make migrate:create MESSAGE=add_{name}_table", file=sys.stderr)

    print()
    print("Next: make migrate && make test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
