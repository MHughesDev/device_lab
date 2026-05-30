---
doc_id: "11.3"
title: "testing strategy"
section: "Quality"
summary: "Testing strategy — pyramid, what to test at each level, when to add tests, and coverage policy."
updated: "2026-04-17"
---

# 11.3 — testing strategy

<!-- Per spec §11.2 and §26.5 -->

**Purpose:** Testing strategy — pyramid, what to test at each level, when to add tests, and coverage policy.

## 11.3.1 Testing pyramid

This project uses a three-layer pyramid. Each layer has a specific job; do not blur the boundaries.

```
        ▲
       /  \
      / E2E \        ← Not in this repo (external contract/smoke only)
     /--------\
    /Integration\    ← apps/api/tests/ (marker: integration)
   /------------\
  /  Unit tests  \   ← apps/api/app/**/tests/ (marker: unit)
 /________________\
```

### Unit tests — `@pytest.mark.unit`

**What:** Pure logic — services, domain functions, schema validators, utility helpers.
**When:** Any function with conditional logic, state transitions, or error paths.
**How:** Mock all I/O (database, HTTP, filesystem). Never hit real infrastructure.
**Location:** `apps/api/app/<module>/tests/test_service.py`, `test_schemas.py`

```python
@pytest.mark.unit
def test_state_transition_invalid_raises():
    with pytest.raises(StateTransitionError):
        invoice_service.transition("draft", "shipped")
```

### Integration tests — `@pytest.mark.integration`

**What:** Router → service → repository → DB. Tests the full in-process stack.
**When:** Every HTTP endpoint needs at least one happy-path and one error-path test.
**How:** Use the `client` fixture (AsyncClient + SQLite in-memory via conftest). No external services.
**Location:** `apps/api/app/<module>/tests/test_router.py`, `apps/api/tests/`

```python
@pytest.mark.integration
async def test_create_invoice_returns_201(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/invoices/", json={...}, headers=auth_headers)
    assert response.status_code == 201
```

### Smoke tests — `@pytest.mark.smoke`

**What:** Post-deploy validation — /health, /ready, key endpoints return expected status codes.
**When:** Run automatically in the deploy pipeline against the live environment.
**How:** Real HTTP against the deployed service. Minimal — should complete in < 30 s.
**Location:** `apps/api/tests/test_smoke.py`

## 11.3.2 Running tests

```bash
make test                    # all tests with coverage
make test-unit               # unit tests only (fast, no DB)
make test-integration        # integration tests only
make test-smoke              # smoke tests only
```

## 11.3.3 Coverage policy

- **Floor:** 55% (enforced in `pyproject.toml` `[tool.coverage.report] fail_under`).
- **Target:** 70% — tracked in `queue/queue.csv` (Q-003).
- **Ratchet:** `make coverage-ratchet` reads `coverage.xml` and compares to the floor. Never lower the floor.
- **Exclusions:** `skills/`, `packages/ai/`, `scripts/` (tools, not application logic).

## 11.3.4 What NOT to test

- External API responses (mock them; test your handling of responses).
- Framework internals (FastAPI routing, SQLAlchemy ORM internals).
- Generated migration files (covered by `make ci-migrate-dry-run`).
- `# pragma: no cover` — use sparingly and only for unreachable defensive paths.

## 11.3.5 Test file conventions

| File | Marker | Scope |
|------|--------|-------|
| `test_router.py` | `integration` | HTTP layer end-to-end |
| `test_service.py` | `unit` | Business logic, no I/O |
| `test_schemas.py` | `unit` | Pydantic validation |
| `test_smoke.py` | `smoke` | Post-deploy health check |
| `conftest.py` | — | Fixtures (no tests) |

## 11.3.6 Fixtures

- **`client`** — `AsyncClient` backed by in-memory SQLite + migrated schema. Defined in `apps/api/tests/conftest.py`.
- **`auth_headers`** — JWT bearer token for a test user.
- **`tenant_headers`** — JWT with `tenant_id` claim for multi-tenancy tests.
- Module-local fixtures go in `apps/api/app/<module>/tests/conftest.py`.

## 11.3.7 When to add a test

Add a test when:
1. You add a new route (at minimum: happy path + 401/403 without auth).
2. You fix a bug (regression test first, then fix).
3. You add a branch or guard condition in a service method.
4. A new error code is added to `exceptions.py`.

Never merge without a test for new behaviour.
