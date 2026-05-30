---
doc_id: "5.16"
title: "initialize repo"
section: "Procedures"
summary: "Documentation-first, queue-first repo initialization from a completed idea.md, driven by the canonical repo_initialize skill."
updated: "2026-05-17"
---

# 5.16 — initialize repo

**Purpose:** Canonical procedure for converting a completed `idea.md` into a refreshed project spec, derived design docs, and initial MVP queue rows. The procedure does **not** write product code — that work is queued.

## Preconditions

- A developer has filled out `idea.md` end-to-end (every applicable section, `N/A` where inapplicable).
- The baseline full-stack app (`apps/api/` + `apps/web/`) is in place.
- The agent has read root `AGENTS.md`, `apps/api/AGENTS.md`, `apps/web/AGENTS.md`, and `queue/QUEUE_INSTRUCTIONS.md`.

## Inputs

- `idea.md` — the canonical human-authored intake contract.

## Outputs

- Refreshed `spec/spec.md` product section (or new product spec appended to template spec).
- Derived design docs under `docs/architecture/`, `docs/api/`, `docs/data/`, `docs/security/`, `docs/operations/`, `docs/testing/`.
- `docs/open-questions.md` populated from `idea.md §19`.
- Initial MVP queue rows in `queue/queue.csv`, ordered as the path from baseline to the MVP defined in `idea.md §4`.
- Blocked `category=human-ops` queue rows for unresolved open questions.
- A PR titled `init: <product name>` summarizing what was initialized and what remains blocked.

## Exact commands

- `make queue:validate`
- `make docs:check`
- `python3 scripts/check_docs_map.py`
- `python3 scripts/repo_self_audit.py`

(No `make idea:*` target exists. Initialization is driven by an AI skill, not a Make orchestrator.)

## Ordered steps

1. Read `idea.md` end-to-end. Triage every section as complete / N/A / incomplete.
2. Surface any blocking gaps (incomplete MVP sections, or `§19` open questions that would change architecture). Stop and report back to the developer if any exist.
3. Run [`skills/init/repo_initialize.md`](../../skills/init/repo_initialize.md) end-to-end. The skill has six phases (triage → spec → docs → ADR → MVP queue → validate) with explicit gates.
4. Run `make queue:validate`, `make docs:check`, `python3 scripts/repo_self_audit.py`.
5. Open one PR titled `init: <product name>` with the skill's handoff summary as the description.

## Acceptance

- Every MVP bullet in `idea.md §4` traces to one or more queue rows.
- Every blocked open question has a `category=human-ops` queue row.
- No file under `apps/api/app/` or `apps/web/src/` was modified by this procedure.
- All listed validation commands pass.

## Related resources

- Canonical skill: [`skills/init/repo_initialize.md`](../../skills/init/repo_initialize.md)
- Invocation prompt: [`prompts/repo_initializer.md`](../../prompts/repo_initializer.md)
- Founding ADR: [`docs/adr/0001-initial-template-architecture.md`](../adr/0001-initial-template-architecture.md)
- Queue lifecycle: [`queue/QUEUE_INSTRUCTIONS.md`](../../queue/QUEUE_INSTRUCTIONS.md)
