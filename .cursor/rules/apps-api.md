---
globs:
  - "apps/api/**"
description: Path-scoped rules for apps/api/. Enforces FastAPI patterns, service/repository boundaries, import conventions, and test co-location.
---

# .cursor/rules/apps-api.md

Rules for **`apps/api/`**: FastAPI layout, layers, DI, schemas vs ORM models, errors, and tests. Align with **[PYTHON_PROCEDURES.md](../../PYTHON_PROCEDURES.md)** and **`apps/api/AGENTS.md`**.

## Module structure

1. Each bounded context has **`__init__.py`**, **`router.py`**, **`models.py`**, **`schemas.py`**, **`service.py`**.
2. **`__init__.py`** exports the **`router`** and key public types.
3. Add **`dependencies.py`** when the module needs non-trivial **`Depends()`** factories.
4. Add **`repository.py`** when persistence logic is large enough to split from **`service.py`**.
5. Cover new behavior with **`apps/api/tests/test_<area>.py`** (or focused module tests).
6. Avoid uncontrolled file sprawl — split subpackages when a context grows.

## Router registration

1. Define **`router = APIRouter(prefix="/...", tags=[...])`** in **`router.py`**.
2. Include routers from **`apps/api/app/main.py`** under a consistent API prefix (e.g. **`/api/v1`**) without duplicating path segments.
3. Keep registration order predictable (e.g. alphabetical by package name).

## Dependency injection

1. Do **not** construct services inline in handlers — use **`Depends()`** factories.
2. DB access uses shared session dependencies (e.g. **`get_db`**) from **`apps/api/app/dependencies.py`**.
3. Auth uses **`get_current_user`** (or stricter deps) from **`auth/dependencies.py`**.
4. Configuration via **`Depends(get_settings)`**, not hidden imports of a global **`settings`** in routers.
5. Place module-specific **`Depends()`** factories in **`dependencies.py`** for that module.

## Pydantic vs SQLAlchemy

1. Request/response shapes live in **`schemas.py`** for that context.
2. Cross-cutting contracts live in **`packages/contracts/`**.
3. SQLAlchemy models live in **`models.py`** — not mixed with API schemas.
4. Naming: **`CreateXRequest`**, **`XResponse`**, etc. — be consistent within the module.
5. Return **validated response models**, not raw ORM rows, at HTTP boundaries.

## Errors

1. Prefer a stable JSON error body (see **`middleware.py`** and **`exceptions.py`**).
2. Services raise **`AppError`** subclasses — routers stay thin.
3. Register or map domain errors in one place so clients see consistent **`code`** / **`message`**.

## Tests

1. Tests live under **`apps/api/tests/`** with clear names: **`test_<unit>_<scenario>_<outcome>`**.
2. Shared fixtures in **`conftest.py`**; factories in **`factories.py`** when helpful.
3. Mark slower integration tests (e.g. **`@pytest.mark.integration`**) per **`pyproject.toml`**.
4. Each public route should have at least one success and one failure case where meaningful.
