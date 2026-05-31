# .cursor/commands/scaffold-module.md

Scaffold a new **bounded context** under **`apps/api/app/<module>/`** with router, schemas, service, models, tests, and registration.

| Field | Value |
|-------|--------|
| **Name** | Scaffold domain module |
| **Description** | Create **`apps/api/app/<module>/`** with FastAPI router, layers, and tests; wire into **`main.py`**; add migration when models change. |
| **Arguments** | **`module_name`** (kebab or snake per convention), **`entities`** (comma list) |
| **Skill** | [`skills/backend/fastapi-router-module.md`](../skills/backend/fastapi-router-module.md) |
| **Machinery** | [`skills/backend/module-scaffolder.py`](../skills/backend/module-scaffolder.py) |
| **Procedure** | [`docs/procedures/scaffold-domain-module.md`](../docs/procedures/scaffold-domain-module.md) |

## Steps

1. Mandatory skill search: read **`skills/backend/fastapi-router-module.md`** and related backend skills.
2. Confirm **`module_name`** and entities; avoid colliding with existing packages.
3. Run **`make scaffold:module`** if defined, **or** invoke **`skills/backend/module-scaffolder.py`** as documented in the skill.
4. Verify created files: **`__init__.py`**, **`router.py`**, **`models.py`**, **`schemas.py`**, **`service.py`**, **`tests/test_<module>.py`** (or project convention).
5. Register the router in **`apps/api/app/main.py`** without duplicating URL prefixes.
6. Add Alembic migration when models change: **`make migrate:create MESSAGE="add <module> tables"`** (or equivalent).
7. Run **`make lint`**, **`make typecheck`**, **`make test`**.
8. Update **`docs/api/endpoints.md`** for new routes.
9. Commit: `feat(<module>): scaffold <module> module`.

## Expected output

- New package under **`apps/api/app/<module>/`**
- Tests passing under **`apps/api/tests/`**
- Migration file under **`apps/api/alembic/versions/`** when schema changed
- Docs updated for public HTTP surface
