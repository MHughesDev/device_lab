# skills/backend/fastapi-router-module.md

<!-- CROSS-REFERENCES -->
<!-- - Machinery: skills/backend/module-scaffolder.py -->
<!-- - Related procedure: docs/procedures/scaffold-domain-module.md -->
<!-- - Related rules: .cursor/rules/apps-api.md -->

**Purpose:** [FULL SKILL] How to add a new FastAPI router/module: file placement, router registration, dependency injection, schema definition, test scaffolding. Per spec §26.4 item 55.

## Purpose

One paragraph. Adding a new FastAPI module is the most common structural change in this repository. This skill ensures every new module follows the canonical layout (router, models, schemas, service, dependencies, tests), is registered correctly in main.py, and follows all PYTHON_PROCEDURES.md conventions.

## When to Invoke

- When adding a new bounded context (from IDEA.md §4.2 or a new queue item)
- When the initialization agent scaffolds domain modules
- When splitting a module that has grown too large
- When adding a new feature area to an existing module

## Prerequisites

- apps/api/AGENTS.md read
- .cursor/rules/apps-api.md read
- PYTHON_PROCEDURES.md §6 (Domain Separation) and §7 (Import Direction) read
- apps/api/app/main.py read (to understand registration pattern)

## Relevant Files/Areas

- `apps/api/app/<module>/` — new module directory
- `apps/api/app/main.py` — router registration
- `apps/api/tests/test_<module>.py` — test file
- `skills/backend/module-scaffolder.py` — machinery for generation
- `apps/api/app/dependencies.py` — shared dependencies

## Step-by-Step Method

Numbered steps:
1. Run `make scaffold:module MODULE=<name>` or invoke `python skills/backend/module-scaffolder.py <name>`
2. Verify all generated files exist:
   - `apps/api/app/<module>/__init__.py` — exports router
   - `apps/api/app/<module>/router.py` — APIRouter with prefix and tags
   - `apps/api/app/<module>/models.py` — SQLAlchemy models with correct base class
   - `apps/api/app/<module>/schemas.py` — Pydantic request/response models (frozen=True for inputs)
   - `apps/api/app/<module>/service.py` — business logic functions/class
   - `apps/api/app/<module>/dependencies.py` — FastAPI Depends() factories (if needed)
   - `apps/api/tests/test_<module>.py` — test stubs
3. Implement router endpoints in router.py:
   - Use Depends(get_current_user) for auth
   - Use Depends(get_db) for database session
   - Return Pydantic response schemas (never raw SQLAlchemy models)
   - Raise AppError subclasses from exceptions.py (not HTTPException directly)
4. Implement models.py:
   - Inherit from Base (from apps/api/app/database.py)
   - Add TenantMixin if tenant-scoped
   - All columns explicitly typed
5. Implement schemas.py:
   - Request schemas: frozen=True, strict validation
   - Response schemas: include all client-visible fields
6. Implement service.py:
   - Pure business logic — no DB queries, no HTTP concerns
   - Accept repository as parameter (DI)
   - Return domain objects or raise domain exceptions
7. Register router in apps/api/app/main.py:
   - `from apps.api.src.<module> import router as <module>_router`
   - `app.include_router(<module>_router, prefix="/api/v1")`
8. Create Alembic migration: `make migrate:create MESSAGE="add <module> tables"`
9. Run `make lint && make typecheck && make test`

## Command Examples

- `make scaffold:module MODULE=invoices` — scaffold the invoices module
- `make migrate:create MESSAGE="add invoice tables"` — create migration
- `make test` — run tests including new module tests
- `python skills/backend/module-scaffolder.py invoices Invoice,LineItem` — direct scaffold

## Validation Checklist

- [ ] All 6 files created (including dependencies.py if needed)
- [ ] Router registered in main.py
- [ ] All endpoints have typed params and response models
- [ ] Service functions have typed signatures
- [ ] All endpoints use Depends(get_current_user)
- [ ] Models inherit Base (and TenantMixin if tenant-scoped)
- [ ] Migration created and tested (alembic upgrade head succeeds)
- [ ] Test stubs implemented with at least happy path + auth failure test
- [ ] make lint passes, make typecheck passes, make test passes

## Common Failure Modes

- **Circular import**: module imports from another module → restructure so shared types are in packages/contracts/. Fix: identify what's shared and move it.
- **Router not registered**: new module exists but endpoints return 404. Fix: check main.py for `app.include_router(...)` call.
- **Raw SQLAlchemy model in response**: client receives unexpected fields. Fix: always use Pydantic response schema in endpoint return type.
- **Missing tenant filter**: tenant-scoped endpoint returns data from all tenants. Fix: add `where(Model.tenant_id == current_tenant_id)` or use TenantMixin.

## Handoff Expectations

All module files committed, router registered, migration tested, tests passing, endpoints documented in docs/api/endpoints.md.

## Related Procedures

docs/procedures/scaffold-domain-module.md

## Related Prompts

prompts/implementation_agent.md, prompts/domain_modeler.md

## Related Rules

.cursor/rules/apps-api.md (all module structure rules), PYTHON_PROCEDURES.md §6 (domain separation), PYTHON_PROCEDURES.md §7 (import direction)

## Machinery

`skills/backend/module-scaffolder.py` — generates all module files from embedded templates. Invoke: `python skills/backend/module-scaffolder.py <module_name> [Entity1,Entity2]` or via `make scaffold:module MODULE=<name>`.
