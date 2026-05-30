---
doc_id: "3.4"
title: "environment vars"
section: "Development"
summary: "Environment variable reference. All vars documented with defaults, read by `apps/api/app/config.py` via Pydantic Settings (§10.3)."
updated: "2026-04-17"
---

# 3.4 — environment vars

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/development/README.md, README.md -->

**Purpose:** Environment variable reference. All vars documented with defaults, read by `apps/api/app/config.py` via Pydantic Settings (§10.3).

## 3.4.1 Overview

Environment variable reference. All vars documented with defaults, read by `apps/api/app/config.py` via Pydantic Settings (§10.3). See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

## 3.4.2 Rules

- **Never** read the environment with `os.getenv()` outside `apps/api/app/config.py`.
- Copy `.env.example` to `.env` for local development; do not commit real secrets.
- After adding or renaming a variable in code, update **both** `.env.example` and this file.

## 3.4.3 Core variables

| Variable | Default (if unset in code) | Notes |
|----------|----------------------------|--------|
| `DATABASE_URL` | SQLite async URL under the repo | See `.env.example` for Postgres example |
| `DATABASE_POOL_SIZE` | `10` | Connection pool size |
| `JWT_SECRET_KEY` | Dev-only placeholder | Must be strong in any shared environment; validator rejects trivial values |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` | |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | |
| `API_DEBUG` | `false` | Only allowed with SQLite per `Settings` validation |
| `API_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list |
| `API_PREFIX` | `/api/v1` | Mount path for versioned routes |
| `LOG_LEVEL` | `INFO` | |
| `LOG_FORMAT` | `text` | |
| `MULTI_TENANCY_ENABLED` | `false` | |
| `RATE_LIMITING_ENABLED` | `false` | |
| `AI_ENABLED` | `false` | Optional AI profile |
| `CHROMA_HOST` / `CHROMA_PORT` | `chroma` / `8001` | When AI/Chroma is used |
| `MCP_ENABLED` | (not read by Settings yet) | Documented in `.env.example` for operators; MCP mounts at `/mcp` when the integration is present |
| `BROKER_URL` | unset | Optional worker profile |

See `apps/api/app/config.py` for the authoritative list and validation rules.

## 3.4.4 Related

- [.env.example](../../.env.example)
- [operations/configuration.md](../operations/configuration.md)
