# skills/testing/pytest-conventions.md

<!-- CROSS-REFERENCES -->
<!-- - Machinery: skills/testing/test-scaffolder.py -->
<!-- - Related rule: .cursor/rules/testing.md -->
<!-- - Related docs: docs/quality/testing-strategy.md -->
<!-- - Related docs: docs/development/testing-guide.md -->

**Purpose:** [FULL SKILL] Pytest project conventions: directory structure, naming, fixtures, markers, conftest patterns, and coverage configuration. Per spec §26.4 item 81.

## Purpose

One paragraph. Consistent pytest conventions are necessary for agents to write tests that actually run, have the right scope, and integrate correctly with CI. This skill defines the complete testing convention for this repository — from directory layout to fixture patterns to coverage thresholds.

## When to Invoke

- Before writing any test (to verify conventions)
- When setting up a new test module for a new bounded context
- When a test is failing for non-obvious reasons (may be fixture scope or async issue)
- When adding new test markers
- When the CI test job is failing

## Prerequisites

pyproject.toml [tool.pytest.ini_options] read. apps/api/tests/conftest.py read. PYTHON_PROCEDURES.md §15 read.

## Relevant Files/Areas

- `apps/api/tests/` — test directory
- `apps/api/tests/conftest.py` — shared fixtures
- `apps/api/tests/factories.py` — test data factories
- `pyproject.toml` — pytest configuration
- `skills/testing/test-scaffolder.py` — generates test stubs

## Step-by-Step Method — Directory Layout

The canonical test directory structure:
```
apps/api/tests/
├── __init__.py          — package marker
├── conftest.py          — shared fixtures (app, client, db, auth)
├── factories.py         — factory functions for test data
├── test_health.py       — tests for health/ module
├── test_auth.py         — tests for auth/ module
├── test_tenancy.py      — tests for tenancy/ module
└── test_<context>.py    — tests for each additional bounded context
```

## Step-by-Step Method — Fixture Patterns

Standard fixtures defined in conftest.py (see apps/api/tests/conftest.py):
1. `app` fixture (scope=session): create FastAPI test app, apply migrations
2. `client` fixture (scope=function): `httpx.AsyncClient(app=app, base_url="http://test")`
3. `db_session` fixture (scope=function): `AsyncSession` with automatic rollback after test
4. `test_user` fixture (scope=function): create user via service, return User model
5. `auth_headers` fixture (scope=function): create JWT for test_user, return {"Authorization": "Bearer <token>"}
6. For multi-tenant tests: `tenant_a`, `tenant_b` fixtures + per-tenant auth headers

## Step-by-Step Method — Naming Convention

Pattern: `test_<unit_under_test>_<scenario>_<expected_outcome>`
- `test_create_invoice_valid_request_returns_201`
- `test_create_invoice_missing_amount_returns_422`
- `test_login_invalid_password_returns_401`
- `test_get_invoice_different_tenant_returns_404`

## Step-by-Step Method — Markers

All markers registered in `pyproject.toml` under `[tool.pytest.ini_options]`:
- `@pytest.mark.unit` — no external deps, fast
- `@pytest.mark.integration` — requires real DB
- `@pytest.mark.smoke` — critical path, run post-deploy
- `@pytest.mark.slow` — >5 seconds, excluded from default run

## Step-by-Step Method — Coverage

Coverage configuration in pyproject.toml:
- `[tool.coverage.run]`: source=["apps/api/app"], omit=["*/alembic/*", "*/__init__.py"]
- `[tool.coverage.report]`: fail_under = floor from docs/quality/coverage-policy.md
- Run: `make test` or `pytest --cov=apps/api/app --cov-report=xml`
- Ratcheting: `python skills/testing/coverage-ratchet.py` updates floor when coverage improves

## Command Examples

- `make test` — full suite with coverage
- `make test:unit` — unit tests only (`pytest -m unit`)
- `make test:integration` — integration tests only (`pytest -m integration`)
- `make test:smoke` — smoke tests only (`pytest -m smoke`)
- `pytest -k "test_invoice" -v` — run tests matching pattern
- `python skills/testing/test-scaffolder.py apps/api/app/invoices/` — scaffold test stubs

## Validation Checklist

- [ ] All tests discoverable by pytest (correct naming and location)
- [ ] Fixtures scoped correctly (function for DB, session for expensive read-only)
- [ ] Markers registered in pyproject.toml
- [ ] Async tests use httpx.AsyncClient (not TestClient)
- [ ] make test passes, coverage above floor
- [ ] No test depends on another test's state (fully isolated)

## Common Failure Modes

- **Event loop closed**: using `TestClient` with async code. Fix: use `httpx.AsyncClient` with `async def test_`.
- **Fixture not found**: conftest.py fixture name mismatch. Fix: verify fixture name in conftest.py exactly.
- **Database state leaked between tests**: using `session` scope for mutable DB fixture. Fix: use `function` scope with rollback.
- **Coverage not counting**: test file not in correct directory. Fix: ensure tests/ is in the source lookup path.

## Handoff Expectations

Tests written, coverage maintained, all markers used correctly, make test passes.

## Related Procedures

docs/procedures/implement-change.md, docs/development/testing-guide.md

## Related Prompts

prompts/test_writer.md

## Related Rules

.cursor/rules/testing.md

## Machinery

`skills/testing/test-scaffolder.py` — analyzes router and service files, generates parametrized test stubs. Invoke: `python skills/testing/test-scaffolder.py apps/api/app/<module>/`
