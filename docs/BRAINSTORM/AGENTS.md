---
doc_id: "19.1"
title: "BRAINSTORM agent contract"
section: "BRAINSTORM"
summary: "Scoped agent rules for docs/BRAINSTORM: read-only vs code; one idea file maps to many queue items."
updated: "2026-04-20"
---

# 19.1 — BRAINSTORM agent contract

**Purpose:** Rules for agents operating in `docs/BRAINSTORM/`. This file is scoped to this directory; it does not override root [`AGENTS.md`](../../AGENTS.md) on repository-wide policy.

## 19.1.1 Instruction hierarchy (this folder)

1. Root [`AGENTS.md`](../../AGENTS.md)
2. This file (`docs/BRAINSTORM/AGENTS.md`)
3. [`PIPELINE-from-brainstorm-to-queue.md`](PIPELINE-from-brainstorm-to-queue.md) when moving from ideation to execution

## 19.1.2 One brainstorm → many queue items (cardinality)

- A **single** brainstorm file under `ideas/` represents the **entire** idea.
- When you move to implementation, you **decompose** that idea into **several** queue rows (each with its own `id`, `summary`, `dependencies`, and usually its own PR). Typical patterns: spike, vertical slice, migration, spec/docs alignment, follow-up.
- Every queue row that implements part of the brainstorm should list the brainstorm file in **`related_files`** (same path for all rows for that idea).
- Record **all** queue IDs in the brainstorm’s **Implementation tracking** table (template section 10).

## 19.1.3 Read-only rule (critical)

- **Do not** edit `apps/`, `packages/`, `deploy/`, `queue/`, root `spec/spec.md`, or other implementation artifacts **solely** because a brainstorm file suggests it.
- **Do** use brainstorms as **input** to planning and to drafting **queue** items when the idea is explicitly marked ready for implementation (see pipeline doc).

Creating or editing files under `docs/BRAINSTORM/` is allowed; that is documentation of ideas, not product code.

## 19.1.4 Creating a new brainstorm

1. Copy [`TEMPLATE-brainstorm.md`](TEMPLATE-brainstorm.md) to `docs/BRAINSTORM/ideas/<YYYY-MM-DD>-<short-slug>.md` (see [`ideas/README.md`](ideas/README.md)).
2. Fill every section; use `TBD` only where intentionally open.
3. Keep the file **structured** — add subsections under the template’s major headings rather than unstructured prose.

## 19.1.5 Turning a brainstorm into work (summary)

When the brainstorm’s **Status** is set to **ready for implementation**:

1. Follow [`PIPELINE-from-brainstorm-to-queue.md`](PIPELINE-from-brainstorm-to-queue.md) end-to-end.
2. Use the queue as the execution lane: [`queue/QUEUE_INSTRUCTIONS.md`](../../queue/QUEUE_INSTRUCTIONS.md).
3. **Code first, then spec/docs:** implement and merge behavior per queue items, **then** update `spec/spec.md` and other docs to match (per pipeline step 6).

## 19.1.6 Handoff

When leaving a brainstorm session, note in the brainstorm file (or queue notes) what changed and what remains open.
