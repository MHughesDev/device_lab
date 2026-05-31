# packages/contracts/pagination.py
"""Pagination parameters, cursor helpers, and list response envelopes."""

from __future__ import annotations

import base64
import json
from typing import Any, cast

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Validated pagination query parameters."""

    model_config = {"frozen": True}

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    cursor: str | None = None
    offset: int | None = Field(None, ge=0)


class PageInfo(BaseModel):
    """Pagination metadata returned with every list response."""

    model_config = {"frozen": True}

    has_next: bool
    has_previous: bool = False
    next_cursor: str | None = None
    previous_cursor: str | None = None
    total_count: int | None = None


class PaginatedResponse[T](BaseModel):
    """Standard envelope for all paginated list endpoints."""

    items: list[T]
    page_info: PageInfo


def encode_cursor(payload: dict[str, Any]) -> str:
    """Encode a cursor payload as a URL-safe base64 string."""

    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> dict[str, Any] | None:
    """Decode a cursor token; return ``None`` if invalid."""

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        data = base64.urlsafe_b64decode(padded.encode())
        return cast(dict[str, Any], json.loads(data.decode()))
    except (json.JSONDecodeError, ValueError):
        return None


def calculate_offset(params: PaginationParams) -> int:
    """Compute SQL OFFSET from page/page_size or explicit offset."""

    if params.offset is not None:
        return params.offset
    return (params.page - 1) * params.page_size


__all__ = [
    "PageInfo",
    "PaginatedResponse",
    "PaginationParams",
    "calculate_offset",
    "decode_cursor",
    "encode_cursor",
]
