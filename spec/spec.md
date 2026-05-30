# Template Repository Specification

**Version:** 5.0  
**Updated:** 2026-05-18  
**Stack:** Python 3.12+, FastAPI, SQLModel, Postgres, Alembic; React 19, Vite, TanStack, Tailwind v4; Docker Compose, optional Traefik  
**Primary operators:** Coding agents (Cursor and compatible tooling). Humans are reviewers, supervisors, and policy maintainers — not the default execution path.

This document is the authoritative specification for the **template repository** — the machine, not any future product built from it. It describes the systemization layer (initialization model, queue semantics, skill/prompt/rule division, documentation invariants) and the full-stack baseline that every initialized product inherits.

Specific product architecture (which database, which auth scheme, which third-party services, etc.) is **out of scope** for this spec. Those decisions belong inside an initialized product, recorded as per-product ADRs at the moment the relevant queue row is executed.

When this spec disagrees with [`docs/adr/0001-initial-template-architecture.md`](../docs/adr/0001-initial-template-architecture.md), the ADR wins. When the ADR disagrees with [`skills/init/repo_initialize.md`](../skills/init/repo_initialize.md), the skill wins (it is the operational source of truth).

---

## 1. Mission

A reusable, agent-first template that lets a developer go from a written product idea to a deployable MVP plan in one human-authoring step and one AI-driven initialization step:

```
developer fills out idea.md  ─►  AI runs skills/init/repo_initialize.md  ─►  refreshed spec + design docs + initial MVP queue rows
                                                                            (no product code yet — that's queued)
```

The template ships with a working full-stack app baseline so the result of initialization is **runnable** before any product-specific code is written. Subsequent product work is executed against the initial queue, one row at a time, each row carrying enough context for an executor to pick up cold.

## 2. Instruction hierarchy

When instructions conflict, resolve in this order (higher overrides lower):

1. Explicit task prompt for the current run.
2. Root [`AGENTS.md`](../AGENTS.md).
3. Scoped agent files: [`apps/api/AGENTS.md`](../apps/api/AGENTS.md), [`apps/web/AGENTS.md`](../apps/web/AGENTS.md), and any directory-local `AGENTS.md`.
4. `.cursor/rules/` (global and path-scoped).
5. `docs/procedures/` — canonical workflows.
6. `skills/` — procedural execution playbooks.
7. `prompts/` — reusable invocation blocks.
8. General docs under `docs/`.

Two sources at the same rank that disagree are a **stop-and-escalate** signal. Do not guess.

## 3. Repository topology

```
.
├── apps/                 # Working full-stack baseline (§5)
│   ├── api/              # FastAPI + SQLModel + Postgres + Alembic + JWT
│   ├── web/              # React 19 + Vite + TanStack + Tailwind v4
│   └── mobile/           # Optional Expo profile (stub)
├── packages/             # Optional Python helpers (contracts, tasks, ai)
├── compose.yml           # db + adminer + backend + frontend + prestart
├── compose.override.yml  # Local dev overrides
├── compose.traefik.yml   # Production Traefik overlay
├── skills/               # Procedural playbooks (§7)
│   └── init/             # Initialization skill (§4)
├── prompts/              # Reusable invocation blocks (§8)
├── docs/                 # Documentation (§9), indexed by docs/DOCS_MAP.md
├── queue/                # CSV work queue + lifecycle docs (§6)
├── spec/                 # This file
├── dev_mcp/              # MicroFast dev MCP server (Cursor/Claude/Codex stdio)
├── .cursor/              # Cursor command/rule/MCP machine surface
├── .github/              # CI/CD workflows + PR/issue templates
├── scripts/              # Make-target backends; deterministic helpers
├── idea.md               # Human-authored product intake (§4)
├── AGENTS.md             # Root agent contract
├── pyproject.toml        # Repo-wide Python tooling config
├── package.json          # Bun workspace pointing at apps/web
└── Makefile              # Canonical command surface
```

The structure is product-neutral. Every initialized product starts from this same shape.

## 4. Initialization model

### 4.1 `idea.md` — product intake contract

`idea.md` is the **single, human-authored** input that drives initialization. A developer fills out every applicable section before invoking the AI. The file separates **intent** (what the product is, who it is for, what it must do for MVP) from **implementation instruction** (which the initializer decides).

Required behavior of `idea.md`:

- One physical file at the repo root. No companion intake files.
- Every applicable section is filled out before initialization. Inapplicable sections are explicitly marked `N/A` with a one-line reason.
- Ambiguity is recorded in §19 "Open questions" and is treated as a first-class output by the initializer, not as a license to invent answers.

The contract sections (canonical numbering, enforced by `idea.md` itself):

1. Product identity
2. Target users
3. Core problem
4. MVP scope (the bullets that drive queue seeding)
5. Explicitly out of scope
6. User stories
7. Core workflows
8. Data and entities
9. Integrations
10. Auth/permissions assumptions
11. Frontend expectations
12. Backend/API expectations
13. Deployment expectations
14. Security/privacy constraints
15. Testing expectations
16. Acceptance criteria for "initialized"
17. Non-functional requirements
18. Hard constraints
19. Open questions
20. Additional context

### 4.2 `skills/init/repo_initialize.md` — canonical initialization skill

A single procedural skill drives initialization. It has six phases, each with an explicit gate:

1. **Triage** `idea.md`. Stop if applicable sections are blank or if architecture-blocking open questions exist.
2. **Spec authoring.** Refresh `spec/spec.md` (or append a product spec section). Every claim must trace back to a specific `idea.md` section via a provenance comment.
3. **Docs derivation.** Generate or refresh `docs/architecture/`, `docs/api/`, `docs/data/`, `docs/security/`, `docs/operations/`, `docs/testing/`, and `docs/open-questions.md` from the spec.
4. **Founding ADR.** If `idea.md` introduces a product-level decision that contradicts a template default, record it as a new ADR inside the initialized product (sequential numbering from 0002; ADR 0001 is reserved for the template's own founding decision).
5. **MVP queue seeding.** Decompose each `idea.md §4` MVP bullet into S/M-complexity queue rows; tag the critical path with `batch=mvp-1`, `mvp-2`, …; create `category=human-ops` blocked rows for any unresolved `idea.md §19` open question.
6. **Validate.** Run `make queue:validate`, `make docs:check`, `python3 scripts/check_docs_map.py`, `python3 scripts/repo_self_audit.py`. Surface failures; do not silently fix.

The skill **never writes product feature code**. Application changes happen by executing the queue rows the skill creates, not during initialization.

### 4.3 What initialization does not do

- Does not run database migrations, install dependencies, or modify CI configuration.
- Does not delete or rewrite the baseline app under `apps/api/` or `apps/web/`.
- Does not silently resolve ambiguity. Ambiguous items become blocked queue rows or `docs/open-questions.md` entries.
- Does not invoke any `make idea:*` target — that command surface has been removed. Initialization is an AI-judged procedure, not a shell orchestrator.

### 4.4 Invocation

A developer who has filled out `idea.md` invokes the initializer via [`prompts/repo_initializer.md`](../prompts/repo_initializer.md), which is a thin wrapper that points at the canonical skill. The output is a single PR titled `init: <product name>` summarizing what was initialized and what remains blocked.

## 5. Full-stack baseline

The template ships with a deployable working app baseline. The baseline is the substrate every initialized product runs on top of.

### 5.1 Backend (`apps/api/`)

| Aspect | Choice |
|---|---|
| Framework | FastAPI 0.114+ with Pydantic v2 |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Database | Postgres 18 |
| Migrations | Alembic |
| Auth | JWT (PyJWT) + pwdlib (argon2/bcrypt) |
| Email | `emails` + Jinja2 + MJML templates |
| Observability | `sentry-sdk[fastapi]` |
| Tests | pytest with fixtures + coverage |
| Lint / format | Ruff |
| Type check | mypy + `ty` |
| Layout | `apps/api/app/{main,api/routes,core,models,crud,alembic}` |

Imports inside the backend use `from app.X import Y`. The package's own pyproject is at `apps/api/pyproject.toml` and is uv-managed.

### 5.2 Frontend (`apps/web/`)

| Aspect | Choice |
|---|---|
| Framework | React 19 + TypeScript |
| Build | Vite 7 (`@vitejs/plugin-react-swc`) |
| Router | TanStack Router (file-based) |
| Server state | TanStack Query |
| Styling | Tailwind v4 + shadcn/ui + Radix primitives |
| Forms | react-hook-form + zod |
| Lint / format | Biome |
| E2E tests | Playwright |
| Typed API client | `@hey-api/openapi-ts` (generated from `/api/v1/openapi.json` via `make generate-client`) |

`apps/web/src/client/` and `apps/web/src/routeTree.gen.ts` are generated; editing them by hand is prohibited.

### 5.3 Orchestration

`compose.yml` + `compose.override.yml` give a local dev stack (db + adminer + backend + frontend + prestart). `compose.traefik.yml` is the production overlay. The baseline does not require a specific cloud — that decision is made per product via `idea.md §13`.

### 5.4 Substituting the baseline

A product can override baseline choices via `idea.md` (e.g. SQLite instead of Postgres). The initializer will record the override and seed rework rows for anything the baseline assumed.

## 6. Queue system

### 6.1 Files

| File | Role |
|---|---|
| `queue/queue.csv` | Open work. Top non-`human-ops` data row is the active item. |
| `queue/queuearchive.csv` | Append-only record of completed / cancelled / superseded items. |
| `queue/QUEUE_INSTRUCTIONS.md` | Authoritative SOP for the queue. |
| `queue/QUEUE_AGENT_PROMPT.md` | Behavior contract for queue-executor agents. |
| `queue/QUEUE_SPLIT_TRIGGERS.md` | Quick reference for when an L row must be decomposed. |

### 6.2 Schema (summary; canonical schema lives in `QUEUE_INSTRUCTIONS.md`)

Required columns: `id`, `category`, `complexity` (`S` or `M`; **`L` is forbidden**), `goal` (≤ 300 chars), `acceptance_criteria` (numbered list), `touch_files` (≤ 2 for S, ≤ 3 for M), `created_date`. Optional but commonly used: `batch`, `phase`, `scope_boundary`, `agent_instructions`, `constraints`, `context_files`, `verification_cmds`, `dependencies`, `notes`.

### 6.3 Lifecycle

Open → In Progress → Done (archive with `status=done` + `completed_date`) → PR merged via `make queue:pr-merge` (or the UI) → branch deleted. Blocked items stay in `queue.csv` with a note explaining the blocker.

### 6.4 Initialization-derived MVP work

Initialization (§4) seeds the initial batch of queue rows. They follow the standard schema with three additional conventions:

- Each row's `context_files` references the docs the initializer produced in phase 3, so executors do not have to re-read `idea.md`.
- Rows on the MVP critical path are tagged `batch=mvp-1`, `mvp-2`, … in dependency order.
- Unresolved `idea.md §19` open questions become `category=human-ops` rows with `notes=blocked_by: open_question`, skipped by `make queue:top-item` but visible to operators.

PRs that materially change a doc the initializer produced must update that doc in the same `touch_files`. Reviewers reject PRs that change behavior without updating the corresponding doc.

## 7. Skills

Skills (`skills/**/*.md`) are **procedural execution playbooks**. Each one is a deterministic step-by-step procedure an agent follows for a specific task.

### 7.1 Required structure per skill

Every skill must contain (case-insensitive):

- A "Purpose" section (either `## Purpose` heading or `**Purpose:**` lead).
- A "When to invoke" section.
- A "Prerequisites" section.

These are enforced by `python3 scripts/repo_self_audit.py` (`skills_headings`).

### 7.2 Categories

Skills are organized by category under `skills/`:

| Category | Example skills |
|---|---|
| `init/` | `repo_initialize.md` — canonical initialization skill. |
| `agent-ops/` | Queue intelligence, task planning. |
| `backend/` | FastAPI router scaffolding, rate limiting, logging, error taxonomy. |
| `frontend/` | Component patterns, route patterns, client regeneration. |
| `devops/` | Image build, image scan, k8s rendering. |
| `security/` | Code scanning, secret handling, RBAC, token lifecycle. |
| `testing/` | pytest conventions, coverage ratchet, test scaffolding. |
| `repo-governance/` | ADR authoring, architecture-design, docs generator/freshness, rule linting. |
| `ai-rag/` | Vector store conventions (optional). |

### 7.3 Skill–prompt relationship

A skill may **reference prompts mid-procedure** ("Use `prompts/<name>.md` during this step"). Skills do **not** absorb prompts; prompts remain independently invokable. Deletion of a prompt requires either replacing every reference to it from skills, or marking those references as broken in `skills_headings`-aware metadata.

## 8. Prompts

Prompts (`prompts/*.md`) are **reusable invocation blocks**. A prompt is something a human or agent can run directly — a self-contained task contract that does not require any surrounding skill.

### 8.1 Required structure per prompt

Every prompt file must contain a YAML front-matter block with at least:

- `purpose:` — one-line statement of what the prompt does.
- `when_to_use:` — when an agent or human should invoke it.

Enforced by `python3 scripts/repo_self_audit.py` (`prompts_frontmatter`, `prompts_title_and_fields`).

### 8.2 Required prompts (minimum)

- `repo_initializer.md` — thin wrapper that invokes `skills/init/repo_initialize.md`.
- `queue_worker_executor.md` — executor contract for picking up a queue row.
- `skill_searcher.md` — task-to-skill matching subroutine.
- `documentation_updater.md`, `task_planner.md`, `reviewer_critic.md`, … as catalog under `prompts/`.

Adding or removing a prompt is governed by [`docs/procedures/add-prompt-template.md`](../docs/procedures/add-prompt-template.md).

## 9. Documentation

### 9.1 Map

Every `.md` under `docs/` (except `DOCS_MAP.md` and files under `docs/generated/`) carries `doc_id` frontmatter and appears as a row in [`docs/DOCS_MAP.md`](../docs/DOCS_MAP.md). Invariants enforced by `python3 scripts/check_docs_map.py`:

- Every doc has `doc_id` frontmatter.
- No two files share a `doc_id`.
- Every map row points at an existing file.
- Every doc has exactly one row.
- Retired IDs do not appear as active entries.

### 9.2 Sections

Sections are numbered by docs subdirectory (`docs/architecture/` → §2, `docs/api/` → §4, `docs/data/` → §21, etc.). The full mapping lives in `DOCS_MAP.md`; this spec does not duplicate it.

### 9.3 Generated docs

`scripts/docs-generate.sh` regenerates `docs/generated/` from sources (Makefile, Settings, compose, k8s, cursor rules, alembic versions) via `skills/repo-governance/docs-generator.py`. Run `scripts/docs-check.sh` to verify there is no drift. Generated docs are **not** the source of truth — they are deterministic indexes derived from the actual sources.

### 9.4 ADR policy

The template ships exactly one ADR: [`docs/adr/0001-initial-template-architecture.md`](../docs/adr/0001-initial-template-architecture.md), which records the **template's own** design decisions. Per-product ADRs (which database, which auth, which payment provider, …) are created **inside an initialized product**, numbered sequentially from 0002. The template does not hardcode product architecture.

New ADRs in **this** template repository should only be added when a decision changes the template's own architecture (initialization model, baseline app substitution, queue semantics, skill/prompt division).

## 10. Command surface

The canonical entrypoint is `make`. Every Make target carries a `## name: description` help line and is documented by `make help`. Critical canonical targets:

| Target | Purpose |
|---|---|
| `make dev` / `make dev-api` | Run FastAPI with uvicorn --reload. |
| `make dev-web` | Run the Vite dev server. |
| `make docker-up` | Bring up the full stack via `compose.yml` + override. |
| `make lint`, `make fmt`, `make fmt-check`, `make typecheck` | Backend Ruff + mypy. |
| `make lint-web`, `make test-web` | Frontend Biome + Playwright. |
| `make test` | Backend pytest with coverage. |
| `make migrate`, `make migrate:create MESSAGE="…"`, `make db-reset` | Alembic + Postgres dev reset. |
| `make queue:peek`, `make queue:top-item`, `make queue:validate`, `make queue:archive-top`, `make queue:pr-merge` | Queue lifecycle commands (see `queue/QUEUE_INSTRUCTIONS.md`). |
| `make docs:check`, `make docs:generate`, `make docs-map-check` | Docs validation and regeneration. |
| `make skills:list`, `make prompt:list`, `make rules:check` | Catalog enumeration and rule linting. |
| `make audit:self` | Repository self-audit (see §11). |
| `make generate-client` | Regenerate `apps/web/src/client/` from the running backend's OpenAPI. |

There is intentionally **no** `make idea:*` target. Initialization is an AI-judged procedure, not a shell orchestrator. See [`prompts/repo_initializer.md`](../prompts/repo_initializer.md) and [`skills/init/repo_initialize.md`](../skills/init/repo_initialize.md).

## 11. Repo self-audit

`python3 scripts/repo_self_audit.py` enforces:

| Check | What it verifies |
|---|---|
| `required_files` | A canonical set of files exists (root `AGENTS.md`, `compose.yml`, queue CSVs, the founding ADR, baseline app entry points, etc.). |
| `queue_validate` | `queue/queue.csv` schema is valid; granularity rules hold. |
| `file_title_comments` | Every `.py` / `.md` / `.sh` / `.yml` outside the vendored substrate (`apps/api/`, `apps/web/`) has a first-line title comment. |
| `skills_headings` | Every skill has Purpose, When to invoke, and Prerequisites sections. |
| `prompts_frontmatter` | Every prompt has a YAML front-matter block. |
| `prompts_title_and_fields` | Every prompt's front-matter contains `purpose:` and `when_to_use:`. |
| `makefile_help` | Every Make target has a `## target: description` help line. |

CI blocks merges on regressions. The audit's `VENDORED_PREFIXES` set carves out `apps/api/` and `apps/web/`, whose files keep upstream conventions and skip the template-systemization first-line-comment rule.

## 12. `.cursor/` — machine control

| Path | Role |
|---|---|
| `.cursor/rules/` | Path-scoped and global rules. Lint with `make rules:check`. |
| `.cursor/commands/` | Cursor commands; `initialize.md` points at the canonical skill. |
| `.cursor/mcp.json` | MicroFast dev MCP server (stdio) configuration. |

## 13. `dev_mcp/` — stdio MCP server

A small Python MCP server (`python -m dev_mcp` or `./dev_mcp/run.sh`) exposes queue/repo tools to MCP-capable clients (Cursor, Claude, Codex). Agents that have MCP available connect before reading the rest of the repo. The connection requirement is documented in root `AGENTS.md` §3.

## 14. Optional capabilities

The full-stack baseline is "always on." Optional capabilities are enabled per product via `idea.md §10`–`§12` and have corresponding skills under `skills/` to drive their implementation:

| Capability | Driven by |
|---|---|
| Mobile (Expo) | `apps/mobile/` (stub) + product queue rows |
| Background workers (Celery + Redis) | `skills/backend/background-jobs.md`, `skills/backend/worker-integration.md` |
| AI/RAG (ChromaDB) | `packages/ai/`, `skills/ai-rag/` |
| Billing (Stripe, …) | per-product ADR + queue rows |
| Multi-tenancy | `skills/security/rbac-tenant-isolation.md` |
| Email/notifications | baseline `emails` + product queue rows |
| Search, storage, analytics, feature flags | per-product queue rows |

The template does **not** ship hardcoded implementations for these. Each is wired up when a product's `idea.md` calls for it.

## 15. Validation- and evidence-first behavior

For every meaningful change:

- Run the relevant Make validation targets (`make lint`, `make fmt-check`, `make typecheck`, `make test`, `make queue:validate`, `make docs:check`, `make audit:self`).
- Update documentation when behavior or operational assumptions change.
- Update queue state per `queue/QUEUE_INSTRUCTIONS.md` lifecycle.
- Hand off with **evidence**: commands run, files changed, PR URL, risks, follow-ups.

CI blocks merges on any of: lint failure, format drift, type errors, test failure, queue validation failure, docs-map drift, repo self-audit regression.

## 16. Non-goals for this spec

This spec deliberately does **not** define:

- Specific product architectures (per-product ADRs decide).
- Profile combinations that are forbidden (profiles compose independently).
- Cloud provider choices (the baseline is cloud-agnostic).
- Test coverage floors for products (each product sets its own in `pyproject.toml`).
- Branding, copy, or UX defaults.

## 17. Document control

| Aspect | Value |
|---|---|
| Spec version | 5.0 |
| Authoritative path | `spec/spec.md` |
| Founding ADR (template architecture) | `docs/adr/0001-initial-template-architecture.md` |
| Canonical initialization skill | `skills/init/repo_initialize.md` |
| Canonical initialization input | `idea.md` (root) |
| Canonical queue SOP | `queue/QUEUE_INSTRUCTIONS.md` |

Changes to the **template machine** require a new template-architecture ADR alongside the spec edit. Changes to **products** are recorded as per-product ADRs inside the initialized product, not here.

---

## 18. Initialized product section — DeviceLab

This section captures the initialized product contract derived from `idea.md`. It complements the template-machine sections above and is the source of truth for DeviceLab queue seeding.

### 18.1 Product summary
<!-- derived from: idea.md §1 §2 §3 -->

DeviceLab is an open-source, local-first, BYOC cloud device platform that lets humans and AI agents provision and operate Linux, Android, Windows, macOS, iOS Simulator, real iOS, and browser testing environments in the user's own AWS account.

The system optimizes for low-friction AI operation over MCP with structured observation and semantic interaction tools, while preserving cost transparency, secret safety, and auditable control in user-owned infrastructure.

### 18.2 End-state scope contract
<!-- derived from: idea.md §4 -->

1. Local install with web UI and MCP gateway.
2. BYOC AWS connect + preflight + bootstrap checks.
3. Seven first-class device families.
4. Capability-aware MCP tool groups and observation pyramid.
5. Low-round-trip interaction contract with screen versioning and batched steps.
6. Recipes + session recording.
7. Identity Broker secret references and elicitation.
8. Streaming/input split (WebRTC + data channel).
9. Cost guardrails and cleanup.
10. Snapshots and forks.
11. Test and artifact pipelines.
12. Evidence/replay traceability.
13. Plugin adapter SPI.
14. First-run wizard.

### 18.3 Non-goals
<!-- derived from: idea.md §5 -->

- No DeviceLab-hosted SaaS, billing, or remote accounts.
- No reseller model or cloud markup.
- No screenshot-loop-first computer-use paradigm.
- No default public inbound runtime ports.
- No proprietary software bundling in OSS core.

### 18.4 Users, permissions, and trust boundaries
<!-- derived from: idea.md §2 §10 §14 §18 -->

- Primary users: solo developers, QA engineers, and AI coding agents using MCP.
- Security model: local operator + scoped MCP client roles with dangerous mode gated.
- Trust boundaries: local control plane, user-owned cloud account, MCP client tokens, runtime-agent mTLS channel.

### 18.5 Domain model overview
<!-- derived from: idea.md §8 -->

Primary entities: `Workspace`, `CloudAccount`, `DeviceTemplate`, `DeviceProfile`, `Device`, `Session`, `McpClient`, `Snapshot`, `Recipe`, `TestRun`, `Artifact`, `Evidence`, `SecretRef`, `CostEstimate`, `AuditEvent`, `WarmPoolSlot`.

### 18.6 Workflow narratives
<!-- derived from: idea.md §7 -->

- First-run onboarding (connect account, preflight, bootstrap, first device, MCP config).
- Human session flow (create device, stream, interact, capture artifacts).
- AI session flow (capability handshake, observe, semantic actions, subscriptions).
- Recipe authoring/replay.
- Cost guardrail and cleanup.
- Diagnostics/handoff export.

### 18.7 Integrations
<!-- derived from: idea.md §9 -->

Core integrations include AWS EC2/SSM/CloudFormation/Pricing/Device Farm, Playwright, Appium drivers, embedded mitmproxy, user-owned coturn, OS keychain, and optional BYOK vision providers.

### 18.8 Constraints and NFRs
<!-- derived from: idea.md §14 §17 §18 -->

- BYOC and local-first are hard constraints.
- No secrets returned to model context.
- Dangerous actions require confirmations and auditing.
- Round-trip-budget tests are first-class acceptance gates.
- Cost transparency target is within +/-10 percent of cloud bill for supported families.
