#!/usr/bin/env bash
# scripts/queue-graph.sh
# Emit Mermaid dependency graph from queue via queue-intelligence.py.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/skills/agent-ops/queue-intelligence.py" graph --repo-root "$ROOT"
