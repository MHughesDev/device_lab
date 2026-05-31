# packages/ai/chromadb_client.py
"""ChromaDB-backed embedding and retrieval (optional dependency: chromadb)."""

from __future__ import annotations

from typing import Any, Protocol


class _AISettings(Protocol):
    """Minimal settings shape; satisfied by apps.api.src.config.Settings."""

    ai_enabled: bool
    chroma_host: str
    chroma_port: int


class ChromaDBClient:
    """Embedding + retrieval using ChromaDB HTTP client."""

    def __init__(self, settings: _AISettings) -> None:
        self._settings = settings
        self._client: Any = None
        self._collection_cache: dict[str, Any] = {}

    @classmethod
    async def from_settings(cls, settings: _AISettings) -> ChromaDBClient:
        return cls(settings)

    def _require_ai(self) -> None:
        if not self._settings.ai_enabled:
            msg = "AI features are disabled (AI_ENABLED=false)"
            raise RuntimeError(msg)

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import chromadb  # noqa: PLC0415
        except ImportError as exc:
            msg = "chromadb package is not installed; pip install -e '.[ai]'"
            raise RuntimeError(msg) from exc
        self._client = chromadb.HttpClient(
            host=self._settings.chroma_host,
            port=self._settings.chroma_port,
        )
        return self._client

    def _collection(self, name: str) -> Any:
        if name not in self._collection_cache:
            client = self._ensure_client()
            self._collection_cache[name] = client.get_or_create_collection(name=name)
        return self._collection_cache[name]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Deterministic pseudo-embeddings for dev when no ML model is configured."""
        self._require_ai()
        if not texts:
            return []
        return [
            [float((hash(t + str(i)) % 997) / 997.0) for i in range(8)] for t in texts
        ]

    async def embed_query(self, query: str) -> list[float]:
        self._require_ai()
        return (await self.embed_texts([query]))[0]

    async def add_documents(
        self, documents: list[dict[str, Any]], collection: str
    ) -> None:
        self._require_ai()
        col = self._collection(collection)
        ids = [str(d.get("id", idx)) for idx, d in enumerate(documents)]
        texts = [str(d.get("text", "")) for d in documents]
        metadatas = [dict(d.get("metadata", {})) for d in documents]
        embeddings = await self.embed_texts(texts)
        col.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

    async def query(
        self, query_embedding: list[float], collection: str, n_results: int
    ) -> list[dict[str, Any]]:
        self._require_ai()
        col = self._collection(collection)
        res = col.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        out: list[dict[str, Any]] = []
        ids_list = res.get("ids", [[]])[0]
        docs_list = res.get("documents", [[]])[0]
        meta_list = res.get("metadatas", [[]])[0]
        dist_list = res.get("distances", [[]])[0] if res.get("distances") else []
        for i, doc_id in enumerate(ids_list):
            item: dict[str, Any] = {"id": doc_id, "text": docs_list[i] if i < len(docs_list) else ""}
            if meta_list and i < len(meta_list):
                item["metadata"] = meta_list[i]
            if dist_list and i < len(dist_list):
                item["distance"] = dist_list[i]
            out.append(item)
        return out

    async def delete_documents(self, ids: list[str], collection: str) -> None:
        self._require_ai()
        col = self._collection(collection)
        col.delete(ids=ids)
