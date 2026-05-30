---
doc_id: "3.8"
title: "module patterns"
section: "Development"
summary: "How to structure bounded-context modules under `apps/api/app/` (router, service, models, tests)."
updated: "2026-04-17"
---

# 3.8 — module patterns

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/development/README.md, README.md -->

**Purpose:** How to structure bounded-context modules under `apps/api/app/` (router, service, models, tests).

## 3.8.1 Overview

How to structure bounded-context modules under `apps/api/app/` (router, service, models, tests). See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

## 3.8.2 Standard layout

Each context under `apps/api/app/<context>/` should include:

| File | Role |
|------|------|
| `__init__.py` | Export `router` and public types |
| `router.py` | HTTP layer only — delegate to `service.py` |
| `models.py` | SQLAlchemy models |
| `schemas.py` | Pydantic request/response models |
| `service.py` | Domain logic and orchestration |
| `dependencies.py` | `Depends()` factories (optional) |

Register the router in `apps/api/app/main.py` under `api_prefix` (default `/api/v1`). Health routes stay outside the versioned prefix.

## 3.8.3 Tests

- Location: `apps/api/tests/`
- Use `httpx.AsyncClient` with the ASGI app for API tests.
- Naming: `test_<unit>_<scenario>_<outcome>`.

## 3.8.4 Related

- [apps/api/AGENTS.md](../../apps/api/AGENTS.md)
- [skills/backend/fastapi-router-module.md](../../skills/backend/fastapi-router-module.md)
- [docs/procedures/scaffold-domain-module.md](../procedures/scaffold-domain-module.md)
