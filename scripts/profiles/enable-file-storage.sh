#!/usr/bin/env bash
# scripts/profiles/enable-file-storage.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$ROOT/packages/storage"
mkdir -p "$PKG"
cat >"$PKG/__init__.py" <<'EOF'
# packages/storage/__init__.py
"""Object storage abstraction."""

from packages.storage.factory import get_storage_provider

__all__ = ["get_storage_provider"]
EOF
cat >"$PKG/base.py" <<'EOF'
# packages/storage/base.py
"""Abstract storage provider."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Upload, download, delete, presigned URLs."""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def download(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_url(self, key: str) -> str:
        raise NotImplementedError
EOF
cat >"$PKG/local.py" <<'EOF'
# packages/storage/local.py
"""Local filesystem storage stub."""

from __future__ import annotations

from pathlib import Path

from packages.storage.base import StorageProvider


class LocalStorage(StorageProvider):
    """Store files under a base directory."""

    def __init__(self, base: Path) -> None:
        self._base = base
        self._base.mkdir(parents=True, exist_ok=True)

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        path = self._base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def download(self, key: str) -> bytes:
        return (self._base / key).read_bytes()

    async def delete(self, key: str) -> None:
        p = self._base / key
        if p.is_file():
            p.unlink()

    async def get_url(self, key: str) -> str:
        return f"file://{self._base / key}"
EOF
cat >"$PKG/s3.py" <<'EOF'
# packages/storage/s3.py
"""S3-compatible storage stub (boto3)."""

from __future__ import annotations

from packages.storage.base import StorageProvider


class S3Storage(StorageProvider):
    """Placeholder — implement with boto3."""

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    async def download(self, key: str) -> bytes:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    async def get_url(self, key: str) -> str:
        raise NotImplementedError
EOF
cat >"$PKG/factory.py" <<'EOF'
# packages/storage/factory.py
"""Resolve storage provider from env."""

from __future__ import annotations

import os
from pathlib import Path

from packages.storage.base import StorageProvider
from packages.storage.local import LocalStorage


def get_storage_provider() -> StorageProvider:
    """Return provider based on STORAGE_PROVIDER."""

    provider = os.environ.get("STORAGE_PROVIDER", "local")
    if provider == "local":
        return LocalStorage(Path(".storage"))
    raise NotImplementedError(f"Unknown STORAGE_PROVIDER={provider}")
EOF
cat >"$PKG/README.md" <<'EOF'
# packages/storage/README.md

File storage profile — implement S3 or other backends behind `StorageProvider`.
EOF
echo "✓ File storage profile enabled — packages/storage/ scaffolded."
