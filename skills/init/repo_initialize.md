# skills/init/repo_initialize.md

**Purpose:** The single, canonical procedural skill that an AI agent runs **after** a developer has filled out `IDEA.md` end-to-end. The skill is documentation-first and queue-first: it does not write product feature code. Its job is to turn a complete `IDEA.md` into (a) design docs, (b) the founding-product ADR(s), and (c) initial MVP queue rows that future agents can execute one at a time.

If `IDEA.md` is incomplete, this skill **stops and queues open-question rows**. It does not invent product decisions.

---

## When to invoke

- The developer has filled out every applicable section of `IDEA.md` and has explicitly asked for repo initialization. (If `IDEA.md` is still the blank stub or only partially filled, run [`skills/init/idea_author.md`](idea_author.md) first.)
- The repo's baseline full-stack app (`apps/api/` + `apps/web/`) is in place — this skill assumes that substrate exists and **plans on top of it**.

Do **not** invoke when:

- `IDEA.md` still has whole sections blank with no `N/A` marker (stop and tell the developer which sections).
- `IDEA.md` §19 "Open questions" lists questions whose answers would change MVP architecture (stop and surface them; do not guess).
- The developer asked only for a docs update — use the standard documentation skills instead.

---

## Prerequisites

- Read this skill, root `AGENTS.md`, and `apps/api/AGENTS.md` + `apps/web/AGENTS.md`.
- Read `IDEA.md` end-to-end.
- Read `queue/QUEUE_INSTRUCTIONS.md` — every queue row this skill creates must conform to its schema.
- Read `docs/adr/template.md` for ADR formatting.
- Confirm `make queue:validate` passes on the current branch before adding rows.

---

## What this skill does NOT do

> **Hard rule: do not write product feature code during initialization.** No edits to files under `apps/api/app/` or `apps/web/src/` that implement product behavior. No new SQLModel models for product entities, no new FastAPI routes for product workflows, no new React components for product screens, no Alembic migrations for product tables. All of that work is **queued** — it is executed later, one row at a time, against the queue rows initialization creates.

The exceptions are limited to non-product configuration: updating `apps/api/.env.example` to reflect new env vars `IDEA.md` introduces, or adding a comment header to an existing baseline file. Any change beyond that is out of scope for initialization and must be deferred to a queue row.

Other behaviors this skill does **not** perform:

- Does not run database migrations, install dependencies, or modify CI configuration.
- Does not delete or rewrite the baseline app. The baseline is the substrate.
- Does not silently resolve ambiguity in `IDEA.md`. Ambiguity becomes an open-question row or a `docs/open-questions.md` entry.

---

## Procedure

The procedure has six phases. Each phase has a single output gate; do not start the next phase until the gate is passed.

---

### Phase 0 — Read and triage `IDEA.md`

1. Read `IDEA.md` end-to-end.
2. For each section, classify:
   - **Complete** — has real content, ready to drive decisions.
   - **N/A** — marked explicitly inapplicable.
   - **Incomplete** — blank, placeholder, or vague.
3. Build a triage report (in chat, not on disk):
   - Which sections are incomplete?
   - Which `§19` open questions block architecture? Which only block implementation? Which are non-blocking?
4. **Gate:** if any incomplete section *blocks an MVP bullet* (§4) or any open question blocks architecture, stop here. Tell the developer exactly which sections/questions are blocking. Do not proceed to Phase 1.

Use `prompts/skill_searcher.md` if you need to find supporting skills for parts of the idea the baseline doesn't already cover (e.g. background jobs, billing, multi-tenancy).

---

### Phase 1 — Author or refresh the project spec

Output: design docs are updated so they are the single authoritative description of what is being built. They must be derivable from `IDEA.md` and contain no information `IDEA.md` doesn't justify.

1. Read the current docs. If the existing content is the **template's own design spec** (not a product spec), preserve template-baseline material in a clearly marked top section and append the product spec below it. Do **not** delete template material that documents the systemization layer.
2. Synthesize the product spec from `IDEA.md` with at minimum these sections:
   - Product summary (1–2 paragraphs derived from §1, §2, §3).
   - MVP definition (verbatim from §4, lightly rewritten as a numbered list).
   - Non-goals (from §5).
   - Users, roles, permissions (from §2, §10).
   - Domain model overview (from §8) — entities, relationships, ownership.
   - Workflow narratives (from §7) — each workflow as numbered steps end-to-end.
   - External integrations (from §9).
   - Constraints and NFRs (from §14, §17, §18).
3. Mark every spec section with a **provenance** comment that names the `IDEA.md` section it derives from, e.g. `<!-- derived from: IDEA.md §4 -->`. This lets reviewers verify nothing was invented.
4. **Gate:** the spec contains no claim that does not trace back to a specific `IDEA.md` section.

---

### Phase 2 — Generate or refresh project docs

Output: every doc under `docs/` that the spec implies is up to date. Docs are produced from the spec, not directly from `IDEA.md`.


| Doc | Source sections | What to write |
|-----|-----------------|---------------|
| `docs/architecture/overview.md` | spec product summary + MVP + workflows | System purpose, archetype, component map (Mermaid), primary data-flow narrative, top 3–5 design decisions |
| `docs/architecture/bounded-contexts.md` | spec domain model + workflows | Each context: owns / does-not-own / exposes / consumes; Mermaid context map |
| `docs/architecture/data-model.md` | spec domain model | Every entity: fields, types, FKs, cardinality, indexes; Mermaid ER diagram |
| `docs/architecture/auth.md` | spec users/roles | Strategy, token lifecycle, permission model, endpoint access matrix |
| `docs/api/endpoints.md` | spec workflows + idea §12 | Every endpoint: method, path, auth, request, response, error codes, example |
| `docs/api/error-codes.md` | spec workflows | Complete error taxonomy: code, HTTP status, message, condition, resolution |
| `docs/data/schema.md` | spec domain model | Plain-language schema description, join patterns, index rationale |
| `docs/security/threat-model.md` | spec constraints + §14 | Top 3–5 threats given archetype + data, mitigations, accepted risks |
| `docs/operations/deployment.md` | idea §13 | Target environments, deploy steps, post-deploy verification |
| `docs/testing/strategy.md` | spec + idea §15 | Unit / integration / smoke / e2e strategy with project-specific concerns |
| `docs/open-questions.md` | idea §19 | One entry per question with Q-id, classification (architecture / implementation / non-blocking), and current status |

Conditional docs (only write real content when the corresponding capability is in scope; otherwise leave with a one-line "Not applicable for this product" note + frontmatter `status: "current"`):

| Doc | Trigger | What to write |
|-----|---------|---------------|
| `docs/architecture/multi-tenancy.md` | §10 says multi-tenant | Isolation model, tenant context propagation, shared-vs-isolated data |
| `docs/architecture/async-workers.md` | §12 mentions background work | Task inventory, retry policy, idempotency, failure handling |
| `docs/architecture/ai-rag.md` | idea §9 or §11 mentions LLM/RAG | Ingestion, embeddings, retrieval, model provider, kill-switch |
| `docs/architecture/billing.md` | §9 mentions payments | Provider, webhook handling, subscription model, retry/dunning |

For every touched doc:
- Update frontmatter: `status: "current"`, `updated: <today>`.
- Reference the spec section it derives from in a top-of-file comment.


---

### Phase 3 — Refresh the founding ADR

Output: `docs/adr/0001-initial-template-architecture.md` is up to date. (This is the template's own founding ADR — it explains the initialization model, not a per-product decision. Per-product ADRs are created at Phase 6.)

1. Read `docs/adr/0001-initial-template-architecture.md`. If it already describes the template's initialization architecture (idea-first → docs-first → queue-first), do not change it.
2. If `IDEA.md` introduced a product-level decision that contradicts a template default (e.g. SQLite instead of Postgres, REST replaced by GraphQL), record it as a **new** ADR:
   - Copy `docs/adr/template.md` to `docs/adr/<NNN>-<kebab-title>.md` (next sequential number).
   - Fill every section (Context, Decision, Consequences, Alternatives, References).
   - Update `docs/adr/README.md` index.

**Gate:** every new ADR has all template sections filled.

---

### Phase 4 — Seed MVP queue rows

Output: `queue/queue.csv` has rows that, taken in order from the top, walk the product from the current baseline to the MVP defined in `IDEA.md` §4.

For each MVP bullet in `IDEA.md` §4:

1. Decompose into queue-row-sized work (≤ S or M complexity per `queue/QUEUE_INSTRUCTIONS.md`).
2. Order rows so each row's `dependencies` are already satisfied by either:
   - the baseline (already in `apps/api/` or `apps/web/`), or
   - an earlier row in `queue/queue.csv` / `queue/queuearchive.csv`.
3. For each row, write the full schema:
   - `id` (next sequential `Q-NNN`)
   - `category` (must match `docs/queue/queue-categories.md`)
   - `complexity` (`S` or `M`; `L` is forbidden and must be split first)
   - `goal` (one or two sentences, ≤ 300 chars)
   - `acceptance_criteria` (numbered list joined with `|`)
   - `touch_files` (≤ 2 for S, ≤ 3 for M)
   - `context_files` (ordered; first listed = highest priority)
   - `verification_cmds` (task-specific)
   - `dependencies`
   - `created_date`
4. For every blocking `§19` open question, add a `category=human-ops` row whose `goal` is "Resolve open question: <question text>" and whose `notes` say `blocked_by: open_question`. These rows are skipped by `make queue:top-item` but are visible in audits.
5. Tag rows that belong on the MVP critical path by including the literal string `mvp` in `category` or `batch` (e.g. `batch=mvp-1`, `batch=mvp-2`, …) so reviewers can see the path at a glance.

The first executable row at the top of `queue/queue.csv` must have:
- all dependencies satisfied,
- `context_files` that all already exist (Phase 2 created them), and
- a `goal` that any agent can pick up from cold-read.

**Gate:** `make queue:validate` passes; `make queue:top-item` returns a row whose `dependencies` are empty or point only to archived rows.

---

### Phase 5 — Validate and report

Run, in order:

1. `make queue:validate`
4. `python3 scripts/repo_self_audit.py`
5. `make lint && make fmt-check` (only if any executable scripts changed)

If any validation fails:
- Roll back the offending file edit when possible.
- Otherwise, record the failure in the handoff and surface it to the developer.

Produce a handoff summary that lists:
- Files written or modified (grouped by phase).
- Each MVP bullet from `IDEA.md §4` mapped to the queue row(s) that fulfill it.
- Every blocked open-question row created, with the source `§19` question.
- Validation command outputs (concise, last 5 lines each).
- The next row at the top of `queue/queue.csv` and a one-sentence summary of what an executor would do next.

---

### Phase 6 — Handoff

The repo is now initialized for the product. Subsequent work follows the standard queue lifecycle in `queue/QUEUE_INSTRUCTIONS.md`. Future product-level ADRs (e.g. "use Stripe for billing") are written when the corresponding queue row is executed, not by this skill.

Do not auto-merge. Open a PR titled `init: <product name>` with the handoff summary as the description.

---

## Cross-references

- Input contract: `IDEA.md`
- Invocation prompt: `prompts/repo_initializer.md`
- Queue rules: `queue/QUEUE_INSTRUCTIONS.md`, `queue/QUEUE_AGENT_PROMPT.md`
- ADR format: `docs/adr/template.md`
- Skill discovery: `prompts/skill_searcher.md`
- Audit: `scripts/repo_self_audit.py`

## Acceptance criteria

Initialization is **not complete** until every item below is true. If any item cannot be satisfied, do not declare initialization done — surface the gap in the handoff and stop.

1. **Required docs are current.** Every doc in the Phase 1 table that applies (architecture overview, bounded contexts, data model, auth, API endpoints, error codes, data schema, threat model, deployment, testing strategy, open questions) has been refreshed and carries `status: "current"` in its frontmatter. Conditional docs (multi-tenancy, async-workers, ai-rag, billing, mobile, frontend) are either filled or carry the standard "Not applicable for this product" stub.
2. **Initial MVP queue rows are seeded.** Every MVP bullet in `IDEA.md §4` is mapped to at least one row in `queue/queue.csv`, tagged with `batch=mvp-1`/`mvp-2`/… in dependency order. The topmost row has empty `dependencies` or dependencies that point only to archived rows.
3. **Blocked open-question rows exist where needed.** Every `IDEA.md §19` open question that the skill judged blocking has a corresponding `category=human-ops` row whose `notes` start with `blocked_by: open_question`.
4. **Founding ADR(s) exist where needed.** For every product-level decision in `IDEA.md` that contradicts a template default, a new ADR has been written at `docs/adr/<NNNN>-<kebab-title>.md` (sequential from 0002) with every template section filled.
5. **`docs/open-questions.md` is populated** with one entry per `IDEA.md §19` item, classified as architecture-blocking / implementation-blocking / non-blocking.
6. **No product feature code was written.** `git diff --stat apps/api/app/ apps/web/src/` is empty for files implementing product behavior. Comment-only header edits and `.env.example` additions are tolerated.
7. **All validation gates pass:**
   - `make queue:validate` exits 0.
   - `python3 scripts/repo_self_audit.py` reports PASS on every check (`required_files`, `queue_validate`, `file_title_comments`, `skills_headings`, `prompts_frontmatter`, `prompts_title_and_fields`, `makefile_help`).
8. **If any audit failure is unavoidable** (e.g. an `IDEA.md` instruction conflicts with a template invariant), the handoff explicitly documents the failure, the reason it cannot be cleanly fixed, and the queue row created to address it. The skill never silently waves audit failures through.

## Validation checklist

Quick checklist mirroring the acceptance criteria above — useful during execution:

- [ ] Every applicable Phase 1 doc has `status: "current"` frontmatter.
- [ ] Every `IDEA.md §4` MVP bullet maps to one or more queue rows tagged `batch=mvp-N`.
- [ ] Every blocking `IDEA.md §19` question has a `category=human-ops` row with `notes=blocked_by: open_question`.
- [ ] `docs/open-questions.md` lists every `§19` item with classification.
- [ ] Founding ADR(s) added for any template-default contradictions.
- [ ] `git diff apps/api/app/ apps/web/src/` shows no product code changes.
- [ ] `make queue:validate` passes.
- [ ] `python3 scripts/repo_self_audit.py` passes (or every failure is documented in the handoff).
