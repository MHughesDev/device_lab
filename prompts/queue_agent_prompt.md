# prompts/queue_agent_prompt.md
---
purpose: "Define the primary behavior contract for agents processing queue-driven work."
when_to_use: "When an agent is executing work selected from queue/queue.csv."
required_inputs:
  - name: "queue_item_row"
    description: "Top queue item payload (typically from make queue:top-item)."
expected_outputs:
  - "Implementation that respects queue row scope and constraints"
  - "Validation evidence and handoff details for operator-led archiving"
validation_expectations:
  - "Mandatory skill search completed before coding"
  - "Queue scope and dependency rules are followed"
constraints:
  - "Executors must not edit queue CSV files or run archive commands"
linked_commands:
  - "make queue:top-item"
linked_procedures:
  - "docs/queue/QUEUE_INSTRUCTIONS.md"
linked_skills:
  - "skills/agent-ops/queue-triage.md"
---

<!-- CROSS-REFERENCES -->
<!-- - Read by: agents processing queue items (injected as context) -->
<!-- - Referenced by: docs/queue/QUEUE_INSTRUCTIONS.md, prompts/queue_processor.md -->
<!-- - Per spec §26.6 item 193 -->

**Purpose:** Executable behavior contract for agents processing queue work.
Canonical lifecycle details remain in `docs/queue/QUEUE_INSTRUCTIONS.md`.

## Pre-Flight Split Check (mandatory before claiming)

Before claiming the top row, answer all five questions. If any answer is NO or
YES where indicated, STOP — do not claim the item. Document
`ESCALATE: split required — [reason]` in PR/handoff for operator follow-up.

| # | Check | Pass condition |
|---|---|---|
| 1 | Is `complexity` `S` or `M`? | Must be S or M. If L or missing: STOP. |
| 2 | Does `touch_files` count respect the limit? | S: ≤2 files. M: ≤3 files. If over: STOP. |
| 3 | Does `goal` contain "and" for two distinct behaviors? | If yes: STOP. |
| 4 | Is `category` = `human-ops`? | If yes: skip this row, advance to next. |
| 5 | Are tests a major deliverable alongside implementation in the same row? | If yes: STOP. |

All five must pass before you proceed to claim the row.

**When you stop:** surface the exact text
`ESCALATE: split required — [brief reason]` in handoff output for the operator.

## Role Definition

State the agent's role and authority scope: "You are processing a queue item from queue/queue.csv. Your authority is bounded by the queue item's summary — you implement exactly what the summary describes, no more, no less. You are not authorized to silently expand scope or skip the mandatory skill search."

### Executor vs operator (CSV is operator-only)

**Implementation agents (executors)** MUST **read** `queue/queue.csv` and `queue/queuearchive.csv` only as needed (e.g. dependency checks). They MUST **never** create, edit, delete, or move rows in those files — including via `make queue:archive-top`, `make queue:archive`, shell redirection, or patch tools. Use **`prompts/queue_worker_executor.md`** as the canonical executor contract.

**Human operators** (or dedicated non-executor automation) perform queue ledger updates: `notes`, **`make queue:archive-top`**, **`make queue:archive`**, **`make queue:validate`** after CSV changes, and **`make queue:pr-merge`**. Executors put the PR URL and evidence in the **PR body** and **handoff**; operators paste into CSV if required.

## Required Read Order

Ordered list of what must be read before processing begins:
1. This file (queue_agent_prompt.md) — complete
2. docs/queue/QUEUE_INSTRUCTIONS.md — complete
3. Run **`make queue:top-item`** — stdout is one JSON line with **every column** of the top open row; parse it completely
4. **`agent_instructions` column** — if non-empty, treat as ordered or unordered steps for the executor; follow together with the **summary** (summary remains the primary contract).
5. **`constraints` column** — if non-empty, contains non-negotiable implementation characteristics (UI/UX interaction behaviors, hex color codes, API contracts, naming conventions, etc.); MUST be respected throughout implementation.
6. **context_files column** — every comma-separated path (repo-relative) in priority order (first listed = highest priority if context is tight); read each before coding and before marking the item complete. Do NOT edit context_files paths — they are read-only. The paths you may write are in **touch_files** only.
7. All files/docs referenced in the goal/acceptance_criteria (if not already covered by context_files)
8. Skills (mandatory search — see below)

For full lifecycle and ledger rules, defer to:
- `docs/queue/QUEUE_INSTRUCTIONS.md`
- `docs/procedures/start-queue-item.md`
- `docs/procedures/archive-queue-item.md` (operator only)

## MANDATORY SKILL SEARCH (Non-Negotiable)

Per spec §4.1 item 13 and AGENTS.md §13 — this step is mandatory and non-negotiable.

Before planning or writing any code:
1. Identify the task domain from the summary (backend, security, testing, infrastructure, etc.)
2. Run `make skills:list` OR read skills/README.md
3. Scan the "When to invoke" section of ALL skills in the relevant category
4. Read every HIGH-relevance skill in FULL before proceeding
5. Note machinery (.py files) as available automation tools
6. Document which skills were found in your handoff notes

**An agent that skips this step is operating out of policy. Stop and complete this step.**

## Execution Rules

Numbered rules for queue item execution:
1. Process ONE item at a time — never start a second item until the first is archived
2. Read the COMPLETE **summary** and non-empty **agent_instructions** — together they form the work contract; partial reads cause scope failures
3. Verify ALL dependencies in queuearchive.csv with status=done before starting
4. If any dependency not met: document in notes as `blocked_by:`, STOP, do not start
5. Plan before coding: acceptance criteria, file impact, risks, scope bounds
6. Validate after each increment: `make lint && make test`
7. Full validation before PR: `make audit:self`
8. STOP and escalate if security or tenancy semantics are ambiguous

## Branch Naming

Required format: `queue/<id>-short-slug` where id is the exact value from the id column. Example: `queue/Q-001-add-invoice-endpoint`.

## PR and archive policy

Use `docs/queue/QUEUE_INSTRUCTIONS.md` as the canonical source for PR and
archive lifecycle details. Executors deliver PR + handoff evidence; operators
perform queue ledger updates and archive commands.

## Blocked Handling

If blocked during work, executors document `blocked_by` in PR/handoff and stop.
Operators update queue notes/ledger per `docs/queue/QUEUE_INSTRUCTIONS.md`.

## Evidence Requirements

Every queue item completion requires:
- Handoff document (per `docs/procedures/handoff.md`)
- PR evidence: files changed, commands run, acceptance criteria verification
- Operator-led queue updates per `docs/queue/QUEUE_INSTRUCTIONS.md`
