---
doc_id: "5.27"
title: "MicroFast development MCP server"
section: "Procedures"
summary: "stdio MCP server for coding agents: queue tools, repo resources, canonical make targets."
updated: "2026-04-17"
---

# 5.3 — MicroFast development MCP server

## 5.3.1 Purpose

Provide a **development-only** Model Context Protocol (MCP) server that packages this template’s agent workflows (queue, skills index, prompts, validation) for **Cursor**, **Claude**, **Codex**, and other MCP-capable clients. It does **not** replace the production API’s optional `fastapi-mcp` mount at `/mcp` ([add-mcp-tool.md](add-mcp-tool.md)).

## 5.3.2 What it exposes

| Kind | Examples |
|------|----------|
| **Tools** | `queue_top_item`, `queue_peek`, `queue_validate`, `read_repo_file`, `list_prompt_files`, `run_make_target` |
| **Resources** | `repo://AGENTS.md`, `repo://README.md`, `repo://skills/README.md`, `repo://queue/QUEUE_INSTRUCTIONS.md`, `repo://prompts/queue_worker_executor.md`, `repo://PYTHON_PROCEDURES.md`, `repo://spec/spec.md`, … |
| **Prompts** | `start_queue_item`, `mandatory_skill_search`, `implement_feature_plan` |

Queue CSV files are **read-only** through this server (same policy as [prompts/queue_worker_executor.md](../../prompts/queue_worker_executor.md)).

## 5.3.3 How to run

After `pip install -e ".[dev]"` (or `./setup.sh`):

```bash
./dev_mcp/run.sh
```

Or: `make dev-mcp` (prints the command). The process speaks **stdio** MCP; configure your client to launch this command.

**Cursor:** `.cursor/mcp.json` registers the `microfast-dev` server using `bash` and `${workspaceFolder}/dev_mcp/run.sh`.

## 5.3.4 Implementation layout

| Path | Role |
|------|------|
| `dev_mcp/server.py` | FastMCP server (tools, resources, prompts) |
| `dev_mcp/run.sh` | Launcher for stdio MCP |
| `dev_mcp/queue_ops/` | Queue CSV logic (stdlib only; used by MCP tools and `scripts/queue_top_item.py`, `scripts/queue_validate.py`) |

## 5.3.5 Validation checklist

- [ ] `make lint`, `make typecheck`, `make test` pass
- [ ] `./dev_mcp/run.sh` starts without import errors (Ctrl+C to exit)
- [ ] MCP client lists tools and resources for `microfast-dev`
