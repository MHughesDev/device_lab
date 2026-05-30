---
doc_id: "5.11"
title: "handle blocked work"
section: "Procedures"
summary: "SOP: Document blockers, escalate, optionally requeue lower items."
updated: "2026-04-17"
---

# 5.11 — handle blocked work

<!-- CROSS-REFERENCES -->
<!-- - Skill: skills/agent-ops/blocked-task-recovery.md -->
<!-- - Rule: .cursor/rules/queue.md (blocked state) -->

**Purpose:** SOP: Document blockers, escalate, optionally requeue lower items. Per spec §26.5 item 146 and §8.3.

## 5.11.1 Purpose

Blocked work must be documented explicitly rather than silently skipped or ignored. The blocker must be escalated to whoever can unblock it.

## 5.11.2 Trigger / When to Use

When the top queue item has unmet dependencies, awaits an external decision, or lacks a required resource.

## 5.11.3 Prerequisites

Blocker clearly identified. queue.csv writable.

## 5.11.4 Exact Commands

`make queue:validate` (after updating notes), **`make queue:top-item`** (next ready item as JSON)

## 5.11.5 Ordered Steps

1. Identify the specific blocker: missing dependency, external API, human decision needed
2. Update the `notes` column of the blocked item:
   `blocked_by: <reason> | owner: <who can unblock> | next_step: <what triggers unblocking>`
3. Do NOT archive the item — it stays in queue.csv
4. Create escalation: GitHub issue OR reply to the relevant PR/discussion
5. Run `make queue:validate` to verify the updated notes are valid
6. (Optional) If policy allows: identify and process next READY item (skip blocked)
7. Document the skip decision in PR notes or AGENTS.md handoff

## 5.11.6 Expected Artifacts / Outputs

queue.csv notes column updated with blocker info. Escalation created (issue or comment).

## 5.11.7 Validation Checks

- [ ] Blocker documented in notes (reason + owner + next step)
- [ ] Item NOT archived
- [ ] Escalation created
- [ ] make queue:validate passes

## 5.11.8 Rollback or Failure Handling

If no next ready item exists and all items are blocked: document in AGENTS.md handoff and wait for human direction.

## 5.11.9 Handoff Expectations

Queue notes updated. Escalation created. Handoff document states which item is blocked, why, and who can unblock.
