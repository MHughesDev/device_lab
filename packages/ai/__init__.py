# packages/ai/__init__.py
"""Optional AI/RAG package; requires ``pip install -e '.[ai]'`` for ChromaDB."""

from __future__ import annotations

try:
    from packages.ai.chromadb_client import ChromaDBClient
    from packages.ai.interfaces import (
        EmbeddingProvider,
        GenerationProvider,
        RetrievalProvider,
    )

    __all__ = [
        "EmbeddingProvider",
        "RetrievalProvider",
        "GenerationProvider",
        "ChromaDBClient",
    ]
except ImportError:
    __all__ = []
