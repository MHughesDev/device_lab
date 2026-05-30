---
doc_id: "3.9"
title: "testing guide"
section: "Development"
summary: "Pytest layout, markers, async tests, and coverage expectations for the API."
updated: "2026-04-17"
---

# 3.9 — testing guide

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/development/README.md, README.md -->

**Purpose:** Pytest layout, markers, async tests, and coverage expectations for the API.

## 3.9.1 Overview

Pytest layout, markers, async tests, and coverage expectations for the API. See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

## 3.9.2 Commands

| Command | Purpose |
|---------|---------|
| `make test` | Full suite with coverage (see `pyproject.toml` threshold) |
| `make test-unit` / `make test:unit` | `TEST_TYPE=unit` |
| `make test-integration` / `make test:integration` | Integration subset |
| `make test-smoke` / `make test:smoke` | Smoke subset |

## 3.9.3 Conventions

- Tests live under `apps/api/tests/` with `test_*.py` modules.
- Async tests use `pytest-asyncio` (mode auto in `pyproject.toml`).
- Use `httpx.AsyncClient` + `ASGITransport` for API tests against `main.app`.
- Prefer explicit fixtures in `conftest.py` for shared clients and DB setup.

## 3.9.4 Coverage

Coverage is enforced in CI (`--cov-fail-under` in `pyproject.toml`). Add tests for any new behavior or bug fix.

## 3.9.5 Related

- [docs/quality/testing-strategy.md](../quality/testing-strategy.md)
- [skills/testing/pytest-conventions.md](../../skills/testing/pytest-conventions.md)
