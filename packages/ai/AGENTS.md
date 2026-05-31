# packages/ai/AGENTS.md

<!-- Per spec §26.9 item 245 — optional AI profile -->

**Purpose:** Scoped agent instructions for the AI package. Per spec §26.9 item 245.

## Scope

Active only when ai-rag profile is enabled (chromadb in dependencies). Root AGENTS.md remains supreme.

## Kill Switch Behavior

All AI operations check AI_ENABLED environment variable. When AI_ENABLED=false: all methods in EmbeddingProvider and RetrievalProvider implementations raise RuntimeError, which the global error handler converts to 503 with a clear message. This is the graceful degradation path when ChromaDB is unavailable.

## Provider Abstraction Rules

Never use chromadb-specific types in service layer code. Always program against EmbeddingProvider and RetrievalProvider protocols. This allows swapping ChromaDB for another vector store without changing application code.

## Testing Without AI Services

Use mock implementations of the Protocol interfaces in tests. Do not start ChromaDB in unit tests. Mark integration tests requiring real ChromaDB with @pytest.mark.integration and skip in non-ai environments.
