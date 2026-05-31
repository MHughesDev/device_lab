# PYTHON_PROCEDURES.md

> **Referenced by:** `AGENTS.md` §10, `.cursor/rules/global.md`
>
> **Purpose:** This document defines the authoritative Python implementation procedures for every Python file in this repository. All agents writing Python code MUST follow these procedures. Composer agents read these procedures and implement accordingly. These are not suggestions — they are enforced by CI (mypy --strict, ruff, pytest, bandit).

---

## Table of Contents

1. [Boundary-First Design](#1-boundary-first-design)
2. [Typed Signatures](#2-typed-signatures)
3. [Shape Declaration and Serialization](#3-shape-declaration-and-serialization)
4. [Interface and Dependency Injection](#4-interface-and-dependency-injection)
5. [Validation at the Edge](#5-validation-at-the-edge)
6. [Domain Separation](#6-domain-separation)
7. [Import Direction and Module Structure](#7-import-direction-and-module-structure)
8. [Explicit State](#8-explicit-state)
9. [Error Policy](#9-error-policy)
10. [Configuration](#10-configuration)
11. [Async](#11-async)
12. [Nullability](#12-nullability)
13. [Immutability by Default](#13-immutability-by-default)
14. [Persistence](#14-persistence)
15. [Testing](#15-testing)
16. [Logging and Observability](#16-logging-and-observability)
17. [CI Enforcement](#17-ci-enforcement)
18. [Code Review](#18-code-review)
19. [Condensed 12-Point Rule Set](#19-condensed-12-point-rule-set)
20. [Refactor Triggers](#20-refactor-triggers)

---

## 1. Boundary-First Design

**Rule:** Define Pydantic schemas before writing any logic. Validate at the edge (ingress/egress). Never pass raw external payloads deep into the system.

**Procedure:**

1. Identify the boundary (HTTP request, queue message, external API response, file upload, env var).
2. Define a Pydantic model for every external payload **before** writing any handler or service function.
3. In the router or adapter, parse the incoming data with `Model.model_validate(raw_data)` immediately — if it fails, raise `422` or equivalent before any logic runs.
4. Pass the **validated model object** (not `dict`, not raw JSON) to service functions.
5. At egress, define a response schema and use `Model.model_validate(result)` before returning.
6. Never allow raw `dict` or `Any` to travel through service or repository layers.

**Rationale:** Boundary validation makes the system's trust boundary explicit and auditable. Internal code can assume data is well-typed.

---

## 2. Typed Signatures

**Rule:** Every non-trivial public function must have fully typed parameters, return type, and documented error expectations. No `Any` without a documented reason. Run `mypy --strict`.

**Procedure:**

1. Every public function signature: `def fn(param: Type, ...) -> ReturnType:`.
2. For async: `async def fn(param: Type) -> ReturnType:`.
3. For functions that may raise, document in docstring: `Raises: ExceptionType — when condition`.
4. `Any` is only acceptable when wrapping truly dynamic data (e.g., JSON deserialization before schema validation). Add `# type: ignore[assignment]  # reason` with explicit reason.
5. Use `TypeVar` and `Generic` for reusable typed containers.
6. Maintain a `py.typed` marker in all packages to enable mypy type checking for consumers.
7. CI runs `mypy --strict` on every PR — no new `type: ignore` without code review approval.

**Enforcement:** `pyproject.toml` `[tool.mypy]` with `strict = true`.

---

## 3. Shape Declaration and Serialization

**Rule:** Use Pydantic models or TypedDict for every cross-module data shape. Named contracts, not anonymous dicts. Normalize dates, enums, and decimals consistently.

**Procedure:**

1. Every data shape crossing a module boundary gets a Pydantic `BaseModel` (or `TypedDict` for simple structures not needing validation).
2. All datetime fields use `datetime` type with timezone awareness; normalize to UTC at ingress.
3. All enum fields use Python `Enum`; never raw strings for categorical values.
4. All decimal/money fields use `Decimal`, not `float`.
5. Serialization: use `model.model_dump(mode="json")` for JSON output; never `dict(model)` or `vars(model)`.
6. Cross-service contracts live in `packages/contracts/` — not in individual apps.
7. Version the contract when backward-incompatible changes are needed (see `packages/contracts/AGENTS.md`).

---

## 4. Interface and Dependency Injection

**Rule:** Prefer `Protocol` over `ABC`. Code against the interface, inject implementations via FastAPI `Depends()` or constructors. Test against the interface, not the implementation.

**Procedure:**

1. Define service interfaces as `Protocol` classes in the module's `interfaces.py` or in `packages/contracts/`.
2. Concrete implementations live in separate files (e.g., `repository.py`, `service.py`).
3. In FastAPI routes, inject via `Depends(get_service_factory)` — never instantiate services directly in route handlers.
4. For non-FastAPI code (scripts, machinery), inject via constructor: `class Service: def __init__(self, repo: RepositoryProtocol): ...`.
5. In tests, create a mock/fake that implements the same `Protocol` — do not patch internals.
6. Never use global mutable state for service instances; use DI container or factory functions.

---

## 5. Validation at the Edge

**Rule:** Validate and normalize once at the boundary. Inside the system, trust typed objects. Validate at egress if correctness of output matters.

**Procedure:**

1. **Ingress** (HTTP, message queue, file): parse → validate → normalize in the adapter/router. Produce trusted typed objects.
2. **Internal**: never re-validate what was already validated at ingress. Trust the type.
3. **Egress** (HTTP response, external API call, queue publish): if output correctness is critical, validate the output schema before sending.
4. Validation failures at ingress raise `ValidationError` (Pydantic) caught by the global error handler → `422 Unprocessable Entity`.
5. Never validate in service layer unless the data originated from a different trust boundary (e.g., reading from DB and re-exposing externally).

---

## 6. Domain Separation

**Rule:** Thin routes (orchestrate only). Business rules in services. Persistence in repositories. Framework code at edges.

**Layers (strict top-down, no skipping):**

```
Router (transport layer)
  → calls Service (domain/business rules)
    → calls Repository (persistence/data access)
      → calls Database (SQLAlchemy session)
```

**Procedure:**

1. **Router functions** (`router.py`): receive request, call service, return response. No business logic. No direct DB access.
2. **Service functions** (`service.py`): contain business rules, orchestration, state transitions. Call repositories. Raise domain exceptions. Manage transaction boundaries.
3. **Repository functions** (`repository.py` or in `service.py` for simple cases): build and execute DB queries. Return domain objects (SQLAlchemy models or Pydantic models). No business logic.
4. **Middleware** (`middleware.py`): cross-cutting concerns (auth, tenant context, logging, correlation IDs). No business logic.
5. **Domain exceptions** (`exceptions.py`): raised by services, caught by routers and translated to HTTP responses.

---

## 7. Import Direction and Module Structure

**Rule:** `router → service → repository`. Never reverse. Shared types in `schemas.py` or `packages/contracts/`. Circular imports are a structural error.

**Canonical module layout:**

```
apps/api/app/<context>/
├── __init__.py          # public API exports (router, key types)
├── router.py            # FastAPI router and endpoint handlers
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic request/response schemas
├── service.py           # business logic
├── dependencies.py      # FastAPI Depends() factories
└── (repository.py)      # optional: separate if persistence is complex
```

**Import rules:**

- `router.py` imports from: `schemas.py`, `service.py`, `dependencies.py`
- `service.py` imports from: `models.py`, `schemas.py` (or `packages/contracts/`), `exceptions.py`
- `repository.py` imports from: `models.py`, `apps/api/app/database.py`
- `schemas.py` imports from: `packages/contracts/` only — never from routers/services
- **Forbidden:** `service.py` importing from `router.py`; `models.py` importing from `service.py`
- Circular imports are a signal of wrong layer assignment — fix the structure, not the import

---

## 8. Explicit State

**Rule:** Use `Enum` or `Literal` for states. Use `dict[State, set[State]]` for transition maps. A `transition()` function enforces the map. Apply to: queue lifecycle, order status, jobs, approvals.

**Procedure:**

1. Define states as a Python `Enum`:
   ```python
   class OrderStatus(str, Enum):
       PENDING = "pending"
       CONFIRMED = "confirmed"
       CANCELLED = "cancelled"
   ```
2. Define allowed transitions as a mapping:
   ```python
   TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
       OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
       OrderStatus.CONFIRMED: {OrderStatus.CANCELLED},
       OrderStatus.CANCELLED: set(),
   }
   ```
3. Implement a `transition(current: State, target: State) -> State` function that validates against the map and raises `InvalidTransitionError` if disallowed.
4. Never mutate state by setting a field directly without calling `transition()`.
5. State enum values in DB are stored as strings (use `sa.Enum` or `sa.String` with enum validation).

---

## 9. Error Policy

**Rule:** Custom exception hierarchy in `exceptions.py`. Base exception carries `code`, `status`, and `message`. Catch at the correct layer. Translate infrastructure errors at adapter boundaries. Never swallow exceptions silently. Log context without secrets.

**Exception hierarchy:**

```python
# apps/api/app/exceptions.py
class AppError(Exception):
    code: str
    status_code: int
    message: str

class NotFoundError(AppError): ...
class ValidationError(AppError): ...
class AuthenticationError(AppError): ...
class AuthorizationError(AppError): ...
class ConflictError(AppError): ...
class ExternalServiceError(AppError): ...
```

**Procedure:**

1. Define all custom exceptions in `apps/api/app/exceptions.py` with `code`, `status_code`, `message`.
2. Services raise domain exceptions (`NotFoundError`, `ConflictError`, etc.) — never HTTP exceptions directly.
3. Routers catch domain exceptions and translate to `HTTPException` (or let the global handler do it).
4. Global exception handler in `middleware.py` catches `AppError` subclasses and returns structured JSON error response.
5. Repository layer catches `SQLAlchemyError` and re-raises as `ExternalServiceError` or specific domain exceptions.
6. **Never:** `except Exception: pass` or logging an exception without re-raising or handling.
7. Log the exception with context: `logger.error("...", exc_info=True, extra={"correlation_id": ..., "user_id": ...})` — never log secrets, tokens, or passwords.

---

## 10. Configuration

**Rule:** Single Pydantic `BaseSettings` in `config.py`. Validate on startup. No `os.getenv()` anywhere except `config.py`. Pass config via dependency injection.

**Procedure:**

1. One `Settings(BaseSettings)` class in `apps/api/app/config.py`.
2. All env vars declared as fields with type annotations, defaults, and descriptions.
3. `@field_validator` for cross-field validation (e.g., database URL format).
4. Instantiate as a module-level singleton: `settings = Settings()` (fails fast on startup if invalid).
5. Expose via FastAPI `Depends(get_settings)` for use in routes.
6. **Forbidden:** `os.getenv("VAR")` anywhere except `config.py`. This makes it impossible to audit which env vars the app reads.
7. `.env.example` documents every var; `scripts/env-var-sync.py` verifies sync.

---

## 11. Async

**Rule:** Route handlers are `async` by default. All I/O uses async libraries. CPU-bound work offloaded via `asyncio.to_thread` or background tasks. Never block the event loop. Use `asyncio.gather` for concurrent independent I/O.

**Procedure:**

1. All FastAPI route handlers: `async def endpoint(...) -> ResponseModel:`.
2. Database operations: use `AsyncSession` from SQLAlchemy async extension.
3. HTTP calls to external services: use `httpx.AsyncClient`, not `requests`.
4. File I/O: use `aiofiles` for large files; `anyio` for other async I/O.
5. CPU-bound work: wrap in `asyncio.to_thread(cpu_bound_fn, args)`.
6. Multiple independent async operations: use `results = await asyncio.gather(op1(), op2())`.
7. **Never:** `time.sleep()` in async code — use `await asyncio.sleep()`.
8. **Never:** synchronous database drivers in async handlers (e.g., `psycopg2` directly — use `asyncpg`).

---

## 12. Nullability

**Rule:** Prefer non-optional types. Use `T | None` not `Optional[T]`. Never return `None` as an error signal. Narrow before use. `mypy --strict` catches unhandled `None`.

**Procedure:**

1. Prefer `str` over `str | None` wherever a value is always present.
2. When `None` is semantically valid (e.g., optional field), use `T | None` (Python 3.10+ union syntax).
3. Do not use `Optional[T]` (the `typing.Optional` form) — use `T | None` directly.
4. When a function might not find a value, return `T | None` and document when `None` is returned — never silently return `None` for errors.
5. Before using a nullable, narrow: `if value is None: raise NotFoundError(...)` or `if value is not None: use(value)`.
6. In Pydantic models, use `Field(default=None)` for optional fields — mypy will enforce that callers handle `None`.
7. **Never:** `value or default_value` when `value` could legitimately be falsy (e.g., `0`, `""`) — use `value if value is not None else default_value`.

---

## 13. Immutability by Default

**Rule:** `frozen=True` on boundary shapes, config, and domain events. Use tuples over lists for fixed collections. Use `Mapping`/`Sequence` in signatures. Make mutation deliberate and localized.

**Procedure:**

1. All Pydantic models representing external input/output: `model_config = ConfigDict(frozen=True)`.
2. `Settings` class: `frozen=True` — configuration never changes at runtime.
3. Domain events: frozen dataclasses or frozen Pydantic models.
4. In function signatures, prefer `Sequence[T]` over `list[T]` and `Mapping[K, V]` over `dict[K, V]` when the function only reads.
5. When mutation is needed (e.g., building a response), use a mutable local variable and convert to immutable at boundary.
6. SQLAlchemy models are mutable (they represent DB state) — that is the expected exception.

---

## 14. Persistence

**Rule:** Queries in repository layer only. Return domain objects, not raw rows. Service owns transaction boundaries. No mixed query + business logic.

**Procedure:**

1. All SQLAlchemy queries live in repository functions (or in `service.py` if no dedicated repository).
2. Repository functions return: SQLAlchemy model instances, Pydantic models, or primitive types — never `Row` objects or raw dicts.
3. Services own `async with session.begin():` transaction boundaries.
4. Repository functions receive `AsyncSession` as a parameter (injected by the service or FastAPI `Depends`).
5. **Never:** query in router handlers or middleware.
6. **Never:** business logic (state transitions, validation, calculations) in repository functions.
7. For tenant-scoped models: always add `.where(Model.tenant_id == tenant_id)` — use `TenantMixin` to enforce this at the model level.

---

## 15. Testing

**Rule:** Unit test domain in isolation. Integration test boundaries. API test contracts. Regression test before fix. Test behavior not implementation. Use factories. Descriptive names.

**Procedure:**

1. **Unit tests** (`test_<module>.py`): test service/domain logic with mocked dependencies. No DB, no HTTP.
2. **Integration tests** (`test_<module>_integration.py`): test with real DB (SQLite in CI), real sessions, real migrations applied.
3. **API tests** (`test_<module>.py` using `httpx.AsyncClient`): test request → response contract. HTTP only — mock external services.
4. **Regression tests**: when a bug is reported, write the failing test first, then fix, then verify the test passes.
5. **Test naming:** `test_<unit_under_test>_<scenario>_<expected_outcome>` e.g., `test_login_invalid_password_returns_401`.
6. **Factories:** use factory functions or `factory_boy` to create test data — never hardcode entity IDs.
7. **No shared mutable state** between tests — use fixtures with proper scope (function > module > session).
8. **Coverage floor:** defined in `docs/quality/coverage-policy.md`; enforced by `scripts/coverage-ratchet.py`.

---

## 16. Logging and Observability

**Rule:** Structured JSON logs. Correlation IDs. Log transitions and boundary events. Mask secrets. Appropriate log levels.

**Procedure:**

1. Use structured logging: `logger.info("event", extra={"key": value, ...})` with a JSON formatter in production.
2. Every request gets a `correlation_id` (UUID) injected by middleware and included in all log records for that request.
3. Log at boundaries: request received, service called with key inputs, response returned.
4. Log state transitions: `logger.info("order_status_changed", extra={"from": old, "to": new, "order_id": id})`.
5. **Never log:** passwords, JWT tokens, API keys, full credit card numbers, or any secret value.
6. Log levels:
   - `DEBUG`: detailed developer information (disabled in production)
   - `INFO`: normal operations, state transitions, significant events
   - `WARNING`: unexpected but handled conditions
   - `ERROR`: failures that affect a user or operation (with `exc_info=True`)
   - `CRITICAL`: system-level failures requiring immediate action
7. Metrics: increment counters for errors, latency histograms for external calls.

---

## 17. CI Enforcement

**Rule:** Formatter, linter, type checker, tests, security scan must all pass. Fail on any violation. No warnings-only. Every PR.

**CI pipeline checks (in order):**

1. `make fmt` — ruff format check (no auto-fix in CI, only check)
2. `make lint` — ruff lint (all rules in `pyproject.toml`)
3. `make typecheck` — mypy `--strict` on all source
4. `make test` — pytest with coverage; fail if below floor
5. `make security:scan` — bandit (SAST) + dependency audit
6. `make image:build` + `make image:scan` — Trivy on built image

**Enforcement rules:**

- No PR merges with failing CI.
- No `# noqa` or `# type: ignore` added without code review comment explaining why.
- Coverage floor only goes up (ratchet) — never decreases without approved exception.
- Security findings classified HIGH or CRITICAL block merge unless documented in `docs/security/accepted-risks.md`.

---

## 18. Code Review

**Rule:** Verify typed boundaries, correct layer assignment, explicit contracts, import direction, `None` handling, tests present. Reject shortcuts that increase ambiguity.

**Code review checklist for Python changes:**

- [ ] All public functions have typed signatures (params + return type)
- [ ] No raw `dict` crossing module boundaries — Pydantic models used
- [ ] Service/repository separation maintained — no queries in routers
- [ ] Import direction correct (`router → service → repository`, never reverse)
- [ ] All `None` values handled explicitly before use
- [ ] Exceptions raised are custom `AppError` subclasses, not generic `Exception`
- [ ] Configuration read from `Settings`, not `os.getenv()`
- [ ] Tests added for new behavior (unit + integration where appropriate)
- [ ] No secrets, credentials, or tokens in code or comments
- [ ] State transitions use the `transition()` function, not direct field assignment
- [ ] Async code uses async I/O — no blocking calls in async functions

**Rejection criteria:** Ambiguity-increasing shortcuts (e.g., `Any` without reason, `pass` in except blocks, magic strings instead of enums, hardcoded config values) are automatic rejection.

---

## 19. Condensed 12-Point Rule Set

Quick reference for agents. Full procedures above take precedence in case of conflict.

1. **Boundary shapes first** — Pydantic models before logic; validate at edge; no raw dicts deep in system
2. **Type every signature** — params, return type, errors; `mypy --strict`; no unexplained `Any`
3. **Named contracts** — Pydantic/TypedDict for cross-module data; normalize dates/enums/decimals
4. **Protocol + DI** — code against interface; inject via `Depends()` or constructor; test against interface
5. **Validate once at edge** — trust typed objects internally; validate egress if correctness matters
6. **Thin routes, fat services** — router orchestrates; service rules; repository persists; no cross-layer leakage
7. **One-way imports** — `router → service → repository`; circulars are structural errors; fix the structure
8. **Enums and transition maps** — `Enum` for states; `dict[State, set[State]]` for allowed transitions; enforce via `transition()`
9. **Custom errors, correct layer** — `exceptions.py` hierarchy; catch at correct layer; translate at adapter; never swallow
10. **Single config source** — `BaseSettings` in `config.py`; `os.getenv()` forbidden elsewhere; DI for access
11. **Async all the way** — async handlers; async I/O; `to_thread` for CPU; `gather` for concurrent ops
12. **Explicit nullability** — `T | None`; never `None` as error signal; narrow before use; strict mypy catches gaps

---

## 20. Refactor Triggers

Refactor when **any** of the following is true:

| Trigger | Signal | Recommended action |
|---------|--------|--------------------|
| Intent no longer obvious | Must re-read 3+ times to understand a function | Extract, rename, add type hints |
| Function does more than one thing | "and" in the function name | Split into focused functions |
| Repeated pattern appears 3+ times | Copy-paste with minor variations | Extract shared utility |
| Service imports from another service | Cross-service direct dependency | Introduce shared contract or event |
| Raw dict passed through 3+ functions | Untyped data traveling far | Define Pydantic model at source |
| Circular import | Import error at runtime | Restructure modules, move shared types |
| Test requires patching internals | `monkeypatch.setattr` on internal function | Refactor to dependency injection |
| Config read in non-config location | `os.getenv()` outside `config.py` | Move to `Settings`, inject via DI |
| `except Exception: pass` | Silent failure | Handle explicitly or log + re-raise |
| State mutation without transition check | Direct field assignment | Add `transition()` guard |
| Function longer than ~50 lines | Complex control flow | Extract private helpers |
| Module larger than ~300 lines | Monolithic file | Split by concern into submodules |

**Refactor policy:** Refactoring is a first-class queue item — not something done silently alongside feature work. If refactor is needed to implement a feature cleanly, create a separate queue item for the refactor, do it first, then implement the feature.
