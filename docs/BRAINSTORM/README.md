---
doc_id: "19.0"
title: "BRAINSTORM overview"
section: "BRAINSTORM"
summary: "Read-only ideation space; one brainstorm file is the whole idea and may spawn many queue rows."
updated: "2026-04-20"
---

# 19.0 — BRAINSTORM overview

**Purpose:** A dedicated area for **thinking** about improvements and new features **without** treating this folder as a source of truth for implementation. Nothing in `docs/BRAINSTORM/` authorizes or requires code changes by itself.

## 19.0.1 One brainstorm file ≠ one queue row

- **One brainstorm file** = **one idea end-to-end** (the full concept, goals, risks, and tracking).
- **One brainstorm** typically becomes **multiple** `queue/queue.csv` rows: slices, spikes, migrations, doc/spec alignment, hardening, etc. Do **not** assume a 1:1 mapping from brainstorm file to a single queue ID.
- Use [`PIPELINE-from-brainstorm-to-queue.md`](PIPELINE-from-brainstorm-to-queue.md) Step 2 to decompose; list every queue ID in the brainstorm template’s **Implementation tracking** table.

## 19.0.2 What this folder is

- **Read-only relative to the codebase:** Agents and humans should **not** implement features or edit production code **because** a file exists here. Implementation always flows through normal controls: queue, PRs, specs, and procedures.
- **Structured ideation:** Each idea is a separate Markdown file, filled from [`TEMPLATE-brainstorm.md`](TEMPLATE-brainstorm.md).
- **Durable and growable:** Brainstorm files are meant to be revised over time as understanding improves.

## 19.0.3 What this folder is not

- Not a substitute for `spec/spec.md`, ADRs, or the CSV queue.
- Not an automatic trigger for CI or deploys.
- Not a place to paste secrets or credentials.

## 19.0.4 Layout

| Path | Role |
|------|------|
| [`AGENTS.md`](AGENTS.md) | Agent contract: how to use this folder and the handoff pipeline |
| [`TEMPLATE-brainstorm.md`](TEMPLATE-brainstorm.md) | Copy this structure for each new brainstorm file |
| [`PIPELINE-from-brainstorm-to-queue.md`](PIPELINE-from-brainstorm-to-queue.md) | Generic steps from “ready to build” → **multiple** queue rows → code → spec/docs updates |
| [`ideas/README.md`](ideas/README.md) | Where individual brainstorm files live and how to name them |

## 19.0.5 Related links

- Queue: [`queue/QUEUE_INSTRUCTIONS.md`](../../queue/QUEUE_INSTRUCTIONS.md)
- Procedures index: [`docs/procedures/README.md`](../procedures/README.md)
