---
doc_id: "3.6"
title: "Init manifest schema"
section: "Development"
summary: "Defines init-manifest.json fields produced from idea.md for deterministic initialization."
updated: "2026-04-17"
---

# 3.6 — Init manifest schema

## 3.6.1 Overview

`init-manifest.json` is produced by `scripts/idea-parser.py` from structured fields in
`idea.md`. It is the **contract** for `scripts/init-from-idea.py` and for agents using
`prompts/repo_initializer.md`.

The manifest is **write-once per initialization** for a given project decision set. To
change profile decisions after init, update `idea.md`, delete `init-manifest.json`, set
INIT_META `initialized: false`, and re-run `make init:from-idea`.

## 3.6.2 Top-level keys

| Key | Type | Description |
|-----|------|-------------|
| `meta` | object | Parser metadata (version, paths, timestamps, hash). |
| `project` | object | Identity fields from §1 (`project_name`, `display_name`, etc.). |
| `archetype` | string | Internal archetype key (e.g. `api_service`, `saas_product`). |
| `primary_database` | string | `sqlite` or `postgresql`. |
| `profiles` | array | Per-profile enablement and source (`explicit` vs `resolved_by_archetype`). |
| `bounded_contexts` | array | Rows from §4.2 (name, entities, description). |
| `resolved_decisions` | object | Flattened orchestration plan (see below). |

### `meta` sub-schema

| Key | Type | Description |
|-----|------|-------------|
| `init_version` | string | Engine version (e.g. `2.0`). |
| `idea_path` | string | Absolute or relative path parsed. |
| `parsed_at` | string | ISO-8601 timestamp. |
| `initialized` | boolean | Always `false` at parse time; orchestrator updates `idea.md` when done. |
| `init_manifest_hash` | string | SHA-256 of canonical JSON (without the hash field), hex digest. |

## 3.6.3 `resolved_decisions` sub-schema

| Key | Type | Description |
|-----|------|-------------|
| `compose_services` | string[] | Logical Compose services (always includes `api`; may include `db`, `redis`, `worker`, `chroma`, `nginx`). |
| `python_dependencies` | string[] | PEP 508 dependency strings to ensure in `[project.dependencies]`. |
| `env_vars` | object | Key → placeholder value for `.env.example` / `.env`. |
| `modules_to_scaffold` | string[] | Snake_case module names under `apps/api/app/`. |
| `profiles_enabled` | string[] | Profile script stems to `source` (`enable-<stem>.sh`). |
| `profiles_discarded` | string[] | Profile script stems for `discard-<stem>.sh`. |
| `queue_seed_rows` | object[] | Rows matching `queue/queue.csv` columns. |
| `ci_additions` | string[] | Logical CI job names (e.g. `tenant_isolation_integration_test`). |
| `use_postgres` | boolean | True when PostgreSQL URL and deps are applied. |
| `archetype_resolved_fields` | string[] | Profile keys filled from archetype defaults (`[ ]` in §5). |
| `open_questions` | string[] | Non-blocking items from §16. |

## 3.6.4 Example: `saas_product` with billing, email, workers

**Scenario:** B2B SaaS with React web UI, Celery workers, Stripe billing, and transactional email. Primary DB is PostgreSQL.

**Annotations (read alongside the JSON):**

- **`meta`**: `init_manifest_hash` is computed by the parser (omit when hand-drafting; parser fills it).
- **`archetype`**: `saas_product` turns on web, multi-tenancy, workers, scheduled jobs, file storage, email, billing, analytics by default in `ARCHETYPE_DEFAULTS`; explicit `[x] no` in §5 overrides.
- **`resolved_decisions.compose_services`**: Logical services the orchestrator activates — `api` always; `db` when Postgres; `redis`+`worker` when workers profile applies; `nginx` when web frontend applies.
- **`queue_seed_rows`**: Each object must match `queue/queue.csv` columns (including **`agent_instructions`** and **`related_files`**; both may be empty strings); `summary` must be empty or ≥ 100 characters for `make queue:validate`.

```json
{
  "meta": {
    "init_version": "2.0",
    "idea_path": "/path/to/repo/idea.md",
    "parsed_at": "2026-04-15T12:00:00+00:00",
    "initialized": false,
    "init_manifest_hash": "ab12cd34…"
  },
  "project": {
    "project_name": "acme-saas",
    "display_name": "Acme SaaS",
    "one_line_pitch": "Multi-tenant B2B subscriptions with Stripe and email onboarding.",
    "repository_slug": "acme/saas"
  },
  "archetype": "saas_product",
  "primary_database": "postgresql",
  "profiles": [
    {
      "profile_key": "web_frontend",
      "script": "web",
      "enabled": true,
      "source": "resolved_by_archetype"
    },
    {
      "profile_key": "email_notifications",
      "script": "email",
      "enabled": true,
      "source": "resolved_by_archetype"
    },
    {
      "profile_key": "workers",
      "script": "workers",
      "enabled": true,
      "source": "resolved_by_archetype"
    },
    {
      "profile_key": "billing",
      "script": "billing",
      "enabled": true,
      "source": "resolved_by_archetype"
    }
  ],
  "bounded_contexts": [
    {
      "name": "billing",
      "entities": "Subscription, Invoice",
      "description": "Stripe-backed billing and invoices."
    },
    {
      "name": "customers",
      "entities": "Customer, Organization",
      "description": "Customer and org records."
    }
  ],
  "resolved_decisions": {
    "compose_services": ["api", "db", "nginx", "redis", "worker"],
    "python_dependencies": [
      "asyncpg",
      "celery[redis]",
      "redis",
      "sendgrid",
      "stripe"
    ],
    "env_vars": {
      "DATABASE_URL": "postgresql+asyncpg://user:password@localhost:5432/dbname",
      "VITE_API_URL": "http://localhost:8000",
      "CELERY_BROKER_URL": "redis://localhost:6379/0",
      "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
      "TENANT_ISOLATION_MODEL": "row_level",
      "EMAIL_PROVIDER": "smtp",
      "SMTP_HOST": "localhost",
      "SMTP_PORT": "1025",
      "SMTP_FROM": "noreply@example.com",
      "STRIPE_SECRET_KEY": "sk_test_REPLACE_ME",
      "STRIPE_WEBHOOK_SECRET": "whsec_REPLACE_ME",
      "STRIPE_PUBLISHABLE_KEY": "pk_test_REPLACE_ME",
      "ANALYTICS_ENABLED": "false",
      "ANALYTICS_WRITE_KEY": "REPLACE_ME"
    },
    "modules_to_scaffold": ["billing", "customers"],
    "profiles_enabled": ["web", "workers", "email", "billing", "multi-tenancy", "scheduled-jobs", "file-storage", "search", "analytics"],
    "profiles_discarded": ["mobile", "ai-rag", "websocket"],
    "queue_seed_rows": [
      {
        "id": "IDEA-001",
        "batch": "1",
        "phase": "1",
        "category": "core-api",
        "summary": "Implement tenant-scoped Customer CRUD in apps/api/app/customers/: models with TenantMixin, repository, service, router, Pydantic schemas, and pytest coverage. Acceptance: list/create/get return correct HTTP status codes; integration test proves row-level isolation between tenants.",
        "agent_instructions": "1) Scaffold module per module-patterns. 2) Add migrations and tests.",
        "dependencies": "",
        "related_files": "",
        "notes": "seeded from init-manifest",
        "created_date": "2026-04-15"
      },
      {
        "id": "IDEA-002",
        "batch": "1",
        "phase": "2",
        "category": "billing",
        "summary": "Wire Stripe webhooks in packages/billing: verify signatures, persist subscription state, idempotent event handling. Acceptance: webhook tests with stripe-cli fixtures; invalid signature returns 400.",
        "agent_instructions": "",
        "dependencies": "IDEA-001",
        "related_files": "",
        "notes": "seeded from init-manifest",
        "created_date": "2026-04-15"
      }
    ],
    "ci_additions": ["tenant_isolation_integration_test"],
    "use_postgres": true,
    "archetype_resolved_fields": ["web_frontend", "email_notifications"],
    "open_questions": ["Confirm Stripe price IDs for each plan tier before go-live."]
  }
}
```

## 3.6.5 Reading order for agents

1. Read `meta.init_version` and `init_manifest_hash` for traceability.
2. Read `resolved_decisions` in full — **no inference from prose in `idea.md`** during execution.
3. Cross-check `open_questions` against the PR risk list.
