#!/usr/bin/env bash
# scripts/profiles/enable-search.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/search"
mkdir -p "$PKG"
cat >"$PKG/__init__.py" <<'EOF'
# packages/search/__init__.py

from packages.search.factory import get_search_provider

__all__ = ["get_search_provider"]
EOF
cat >"$PKG/base.py" <<'EOF'
# packages/search/base.py
"""Search provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SearchProvider(ABC):
    """Index and query documents."""

    @abstractmethod
    async def index(self, doc_id: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, doc_id: str) -> None:
        raise NotImplementedError
EOF
cat >"$PKG/meilisearch_provider.py" <<'EOF'
# packages/search/meilisearch_provider.py
"""Meilisearch stub."""

from __future__ import annotations

from typing import Any

from packages.search.base import SearchProvider


class MeilisearchProvider(SearchProvider):
    async def index(self, doc_id: str, payload: dict[str, Any]) -> None:
        _ = (doc_id, payload)

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        _ = limit
        return [{"id": "stub", "query": query}]

    async def delete(self, doc_id: str) -> None:
        _ = doc_id
EOF
cat >"$PKG/postgres_fts.py" <<'EOF'
# packages/search/postgres_fts.py
"""PostgreSQL full-text search stub."""

from __future__ import annotations

from typing import Any

from packages.search.base import SearchProvider


class PostgresFTSProvider(SearchProvider):
    async def index(self, doc_id: str, payload: dict[str, Any]) -> None:
        _ = (doc_id, payload)

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        _ = limit
        return []

    async def delete(self, doc_id: str) -> None:
        _ = doc_id
EOF
cat >"$PKG/factory.py" <<'EOF'
# packages/search/factory.py
"""Resolve search provider."""

from __future__ import annotations

import os

from packages.search.base import SearchProvider
from packages.search.meilisearch_provider import MeilisearchProvider


def get_search_provider() -> SearchProvider:
    p = os.environ.get("SEARCH_PROVIDER", "meilisearch")
    if p == "meilisearch":
        return MeilisearchProvider()
    raise NotImplementedError(p)
EOF
cat >"$PKG/README.md" <<'EOF'
# packages/search/README.md

Search profile — Meilisearch or PostgreSQL FTS.
EOF
echo "✓ Search profile enabled — packages/search/ scaffolded."
