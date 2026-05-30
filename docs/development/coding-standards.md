---
doc_id: "3.1"
title: "coding standards"
section: "Development"
summary: "Python and API coding standards for this repository (typing, style, security)."
updated: "2026-04-17"
---

# 3.1 — coding standards

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/development/README.md, README.md -->

**Purpose:** Python and API coding standards for this repository (typing, style, security).

## 3.1.1 Overview

Python and API coding standards for this repository (typing, style, security). See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

## 3.1.2 Style and lint

- **Formatter / linter:** Ruff (`make fmt`, `make lint`). Line length 88; target Python 3.12.
- **Types:** mypy strict (`make typecheck`). Avoid `Any` unless justified.

## 3.1.3 API code

- Routers delegate to services; no direct DB access in handlers.
- Use `Depends(get_settings)` and `Depends(get_db)` from shared dependencies.
- Stable error responses via shared exception handlers (`packages/contracts/errors.py` patterns).

## 3.1.4 Security

- No secrets in source; configuration only via `Settings` in `apps/api/app/config.py`.
- Follow [docs/security/secrets-management.md](../security/secrets-management.md).

## 3.1.5 Related

- [PYTHON_PROCEDURES.md](../../PYTHON_PROCEDURES.md) (if present at repo root)
- `.cursor/rules/` — automated enforcement
