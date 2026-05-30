---
doc_id: "7.3"
title: "ADR-0001 initial template architecture"
section: "ADR"
status: "current"
updated: "2026-05-17"
---

# 7.3 — ADR-0001: Initial template architecture

**Status:** Accepted

**Date:** 2026-05-17

## Context

This repository is a **template machine**: a reusable starting point a developer can clone, fill out, and turn into a real product. The template ships with:

- a working full-stack baseline (FastAPI + React) under `apps/api/` and `apps/web/`,
- an agent-first systemization layer (`AGENTS.md`, `skills/`, `prompts/`, `docs/`, `queue/`),
- and a documented procedure that converts a completed `idea.md` into project docs and queue rows.

There are many viable ways to organize "initialization." This ADR records the decisions that define **this template's** initialization architecture so future contributors do not need to re-derive them.

## Decision

### 1. `idea.md` is the canonical, human-authored product intake contract

A single root file, `idea.md`, captures the developer's product intent end-to-end. It is filled out by a human before any AI runs. It separates **intent** (what the product is and who it is for) from **implementation instruction** (how to build it). The initializer treats every section as user intent and refuses to invent answers when sections are blank.

### 2. `skills/init/repo_initialize.md` is the canonical AI initialization skill

Initialization is driven by a **single procedural skill**, not a phased pipeline of many skills. The skill is deterministic enough to follow step by step, and explicit about its gates (where it stops, what it produces, what it never touches). A thin prompt, `prompts/repo_initializer.md`, exists only as the invocation contract that points at the skill.

### 3. Initialization is documentation-first and queue-first

The skill produces, in order: a refreshed product spec, derived design docs (architecture / API / data / security / testing / operations), founding product ADRs where the idea contradicts a template default, and finally an ordered set of MVP queue rows. The queue is derived from the **initialized docs**, not directly from `idea.md` notes. Product feature code is **not** written during initialization — it is queued.

### 4. Ambiguity is a first-class output, not silent guesswork

When `idea.md` is incomplete or `§19` open questions block decisions, the initializer creates blocked `category=human-ops` queue rows and adds `docs/open-questions.md` entries. It does not silently choose product directions.

### 5. Prompts and skills have distinct roles

- **Prompts** (`prompts/*.md`) are reusable task blocks that humans or agents can invoke directly.
- **Skills** (`skills/**/*.md`) are procedural execution playbooks that may reference prompts mid-procedure (e.g. "Use `prompts/skill_searcher.md` for this step").

Skills do not absorb prompts. Prompts are not collapsed into skills. Each remains independently invokable.

### 6. The full-stack app baseline is the deployable substrate

`apps/api/` (FastAPI + SQLModel + Postgres + Alembic + JWT) and `apps/web/` (React 19 + Vite + TanStack + Tailwind v4) ship as a working baseline. Initialization plans **on top of** the baseline; it does not regenerate it. The baseline gives every initialized product a deployable starting state before any product-specific code is written.

### 7. Product-specific architecture decisions are deferred to per-product ADRs

This template repository holds exactly one ADR — this one — that documents the **template's** design decisions. Product-specific decisions (which database, which auth strategy, whether to use Stripe, etc.) are recorded as new ADRs **inside the initialized product**, authored when the relevant queue row is executed. The template does not hardcode product architecture.

## Consequences

**Easier**

- A developer with a clear product idea fills one file, asks an AI to run one skill, and gets a deterministic set of docs + ordered queue.
- Future agents can pick up the top queue row and execute it without re-reading the entire repo, because the row's `context_files` already point at docs initialization produced.
- The template repo stays product-agnostic; nothing about a specific future product is hardcoded.

**Harder**

- The initializer cannot mask ambiguity by guessing. Half-filled `idea.md` files produce blocked queue rows rather than running implementations — a deliberate slowdown when the input is weak.
- Maintaining the baseline (`apps/api/` + `apps/web/`) is a real responsibility: when it drifts, every product initialized from this template is affected.

**Risks accepted**

- A developer can override the substrate (e.g. replace Postgres with SQLite) via `idea.md`, but the initializer will create rework rows for things the baseline assumed. This is recorded explicitly rather than mitigated by the template machine.

**Follow-up work**

- Future ADRs in this template repository should be rare — limit them to changes that affect the **template's** architecture (e.g. swapping the baseline frontend framework). Per-product ADRs live inside initialized products, not here.

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Multi-phase init skill pipeline (idea-validator → archetype-mapper → profile-resolver → queue-seeder → env-generator) | Required agents to coordinate across many small skills and a manifest file; high token cost, fragile sequencing, and large surface for ambiguity. A single procedural skill with explicit phases is easier to read, follow, and audit. |
| `make idea:execute` orchestrator | Hid AI judgment behind a shell command, encouraging the false expectation that initialization is mechanical. Making the AI skill the entry point keeps it honest: initialization requires reasoning, and the human can review every artifact before merge. |
| Treat `idea.md` as a draft that the AI completes | Inverted the intent contract — the AI would start inventing product decisions whenever the human input was thin. The current rule (developer fills it out fully, AI surfaces gaps as blocked rows) keeps authorship aligned with accountability. |
| Hardcode product archetypes (API service, full-stack, marketplace, …) into the template | Pre-committed every initialized product to a template-defined shape. The full-stack baseline + `idea.md`-driven decisions cover the same surface without pinning a product taxonomy into the template. |

## References

- Input contract: [`/idea.md`](../../idea.md)
- Canonical skill: [`skills/init/repo_initialize.md`](../../skills/init/repo_initialize.md)
- Invocation prompt: [`prompts/repo_initializer.md`](../../prompts/repo_initializer.md)
- Procedure: [`docs/procedures/initialize-repo.md`](../procedures/initialize-repo.md)
- Queue lifecycle: [`queue/QUEUE_INSTRUCTIONS.md`](../../queue/QUEUE_INSTRUCTIONS.md)
- ADR template: [`docs/adr/template.md`](template.md)
