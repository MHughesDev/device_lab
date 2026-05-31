# apps/api — Backend AGENTS scope

This is the DeviceLab FastAPI backend service. It uses **SQLModel**
(SQLAlchemy + Pydantic) on Postgres, Alembic migrations, and an
auto-generated OpenAPI spec that drives the typed client in `apps/web`.
The DeviceLab control plane — device FSM, MCP gateway, adapters, cost
guardrails, audit log — will be built into this app.

> Root `AGENTS.md` (one level up) is authoritative. This file scopes the
> backend conventions only. When conflicts arise between this file and the
> root `AGENTS.md`, root wins (see section 2 of the root AGENTS.md).

## Layout

```
apps/api/
├── app/                       # Python package (import as `app.*`)
│   ├── main.py                # FastAPI app factory + router mount
│   ├── api/                   # HTTP routes
│   │   ├── deps.py            # FastAPI dependencies (current_user, db)
│   │   ├── main.py            # api_router that aggregates all routes
│   │   └── routes/            # login, users, items, utils, private
│   ├── core/                  # config, security, db engine
│   ├── alembic/               # migration env + versions/
│   ├── crud.py                # database CRUD helpers
│   ├── models.py              # SQLModel ORM + Pydantic schemas in one
│   ├── backend_pre_start.py   # wait-for-db on startup
│   ├── initial_data.py        # seeds first superuser
│   ├── tests_pre_start.py     # wait-for-db before pytest
│   ├── utils.py               # email + token helpers
│   └── email-templates/       # MJML + built HTML
├── tests/                     # pytest suite (api / crud / scripts / utils)
├── scripts/                   # format/lint/test/prestart shell scripts
├── alembic.ini
├── Dockerfile
├── pyproject.toml             # backend deps (uv-managed)
└── README.md
```

## Required reading before changing backend code

1. Root `AGENTS.md`
2. This file
3. `apps/api/README.md`
4. `spec/spec.md` for any DeviceLab domain work
5. Any matching skill under `skills/backend/`

## Conventions

- **One model file:** SQLModel + request/response shapes live in
  `app/models.py`. Do not split into `schemas.py` unless an ADR documents the
  reason.
- **Routes:** add new endpoints under `app/api/routes/<name>.py`, then mount
  in `app/api/main.py` (`api_router.include_router(...)`).
- **Database access:** use the `SessionDep` from `app/api/deps.py`; do not
  open ad-hoc engines.
- **Migrations:** every schema change ships with an Alembic revision. Use
  `make migrate:create MESSAGE="<change>"` and review the generated SQL
  before committing.
- **Auth:** the default scheme is OAuth2 password flow + JWT. Look at
  `app/core/security.py` and the `login` route.
- **Config:** all env vars are validated by `app/core/config.py` via
  `pydantic-settings`. Add new vars there and update `.env.example`.
- **Tests:** put unit tests next to the feature in `tests/`; use
  `tests/conftest.py` fixtures. Run `make test`.

## Common commands

| Task                          | Command                                  |
| ----------------------------- | ---------------------------------------- |
| Run API locally               | `make dev` (or `make dev-api`)           |
| Lint                          | `make lint`                              |
| Format                        | `make fmt`                               |
| Type check                    | `make typecheck`                         |
| Run tests with coverage       | `make test`                              |
| Create migration              | `MESSAGE="add foo" make migrate:create`  |
| Apply migrations              | `make migrate`                           |
| Reset dev DB                  | `make db-reset`                          |
| Run the full stack (Docker)   | `make docker-up`                         |

## Frontend client generation

After changing routes or schemas, regenerate the typed client used by
`apps/web`:

```
make generate-client
```

This calls `openapi-ts` against the live `/api/v1/openapi.json` of a running
backend and writes to `apps/web/src/client/`.
