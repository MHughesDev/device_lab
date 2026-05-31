---
globs:
  - "**/tests/**"
  - "**/test_*"
  - "**/*_test.py"
description: Testing standards. Coverage expectations, naming conventions, fixture patterns, mock boundaries.
---

# .cursor/rules/testing.md

Pytest and coverage conventions. See **`docs/quality/coverage-policy.md`**, **`skills/testing/pytest-conventions.md`**, **`PYTHON_PROCEDURES.md`** §15.

## Naming

1. Tests: **`test_<unit>_<scenario>_<expected_outcome>`**.
2. Files: **`test_<module>.py`**; integration suites may use **`*_integration.py`** naming when helpful.
3. Parametrize with readable **`ids=`**.

## Fixtures

1. Default **`function`** scope; avoid shared mutable state.
2. **`session`** only for expensive immutable setup — document why.
3. DB tests use isolated sessions/transactions per test where possible.

## What to mock

1. **Unit** tests mock I/O boundaries (HTTP, SMTP, external SDKs).
2. **Integration** tests use real DB fixtures (e.g. SQLite for CI) and real app wiring.
3. Prefer **interfaces/DI** over deep **`monkeypatch`** when feasible.

## Async

1. Use **`pytest-asyncio`** as configured in **`pyproject.toml`**.
2. Exercise ASGI apps with async HTTP clients per project conventions.

## Coverage

1. Respect the floor in **`docs/quality/coverage-policy.md`** — do not lower it without process.
2. New modules should arrive with meaningful tests; exclude boilerplate **`__init__.py`** lines per config.

## Markers

Register markers in **`pyproject.toml`**: e.g. **`integration`**, **`slow`**, **`smoke`**, as used by this repo.
