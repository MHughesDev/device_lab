#!/usr/bin/env bash
# scripts/profiles/enable-ai-rag.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AI="$ROOT/packages/ai"
mkdir -p "$AI"
if [[ ! -f "$AI/chromadb_client.py" ]]; then
  cat >"$AI/chromadb_client.py" <<'EOF'
# packages/ai/chromadb_client.py
"""Stub ChromaDB client — replace with real integration."""

from __future__ import annotations


class ChromaDBClient:
    """Placeholder."""

    def ping(self) -> bool:
        return True
EOF
fi

python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
dc = root / "docker-compose.yml"
text = dc.read_text()
if "chromadb/chroma" in text:
    print("chroma service already present")
    raise SystemExit(0)
block = """

  chroma:
    image: chromadb/chroma:latest
    profiles:
      - ai
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
"""
marker = "\n\nvolumes:\n  api_data:"
if marker not in text:
    raise SystemExit("docker-compose.yml: expected root volumes section marker")
text = text.replace(marker, block + marker, 1)
if "chroma_data:" not in text:
    text = text.replace("  pg_data:", "  pg_data:\n  chroma_data:", 1)
dc.write_text(text)
print("Added chroma service to docker-compose.yml")
PY

echo "✓ AI/RAG profile enabled — ChromaDB service added to Compose."
