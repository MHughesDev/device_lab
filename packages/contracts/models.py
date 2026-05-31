# packages/contracts/models.py
"""Shared cross-context Pydantic contracts (errors, pagination envelopes)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from packages.contracts.errors import ErrorCode
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base model with ORM-friendly defaults."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampMixin(BaseModel):
    """Created/updated timestamps for resources."""

    created_at: datetime
    updated_at: datetime | None = None


class IdentifiedMixin(BaseModel):
    """Primary key mixin."""

    id: UUID


class ErrorDetail(BaseSchema):
    """Structured error payload."""

    model_config = ConfigDict(frozen=True)

    code: ErrorCode | str
    message: str
    field: str | None = None
    detail: dict[str, Any] | None = None


class ErrorResponse(BaseSchema):
    """Standard API error envelope."""

    model_config = ConfigDict(frozen=True)

    error: ErrorDetail


class PagedResponse[T](BaseSchema):
    """Paginated list response."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=500)
    next_cursor: str | None = None
    has_next: bool = False
