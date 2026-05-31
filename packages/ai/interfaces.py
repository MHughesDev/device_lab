# packages/ai/interfaces.py
"""Protocol interfaces for optional AI/RAG providers."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input string."""

    async def embed_query(self, query: str) -> list[float]:
        """Return a single embedding for search."""


@runtime_checkable
class RetrievalProvider(Protocol):
    async def add_documents(
        self, documents: list[dict[str, Any]], collection: str
    ) -> None:
        """Ingest documents (ids, text, metadata) into a collection."""

    async def query(
        self, query_embedding: list[float], collection: str, n_results: int
    ) -> list[dict[str, Any]]:
        """Return nearest neighbors with scores."""

    async def delete_documents(self, ids: list[str], collection: str) -> None:
        """Remove documents by id."""


@runtime_checkable
class GenerationProvider(Protocol):
    async def generate(self, prompt: str, context: list[str] | None = None) -> str:
        """Optional LLM text generation."""
