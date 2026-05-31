# skills/agent-ops/blocked-task-recovery.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedure: docs/procedures/handle-blocked-work.md -->
<!-- - Related rule: .cursor/rules/queue.md -->

**Purpose:** How to handle blocked work without silently skipping or losing the item. Per spec §26.4 item 43.

## Purpose

One paragraph describing the skill. State that blocked work must be documented in the queue notes and escalated — never silently dropped, and never processed out of order without policy authorization.

## When to Invoke

When the top queue item has unmet dependencies, external blockers (waiting on human decision, external API, third-party), or is explicitly waiting for another team's output.

## Prerequisites

queue.csv accessible, QUEUE_INSTRUCTIONS.md read, blocker identified and documented.

## Relevant Files/Areas

queue/queue.csv (notes column), docs/procedures/handle-blocked-work.md, queue/QUEUE_INSTRUCTIONS.md

## Step-by-Step Method

Numbered steps:
1. Identify the specific blocker: dependency not done, external decision needed, missing credential
2. Update the `notes` column of the blocked item: "blocked_by: [reason] — owner: [who can unblock] — next_step: [what triggers unblocking]"
3. Do NOT archive the item — it stays in queue.csv
4. Escalate: create a GitHub issue or queue the escalation in the notes
5. Optionally: if policy allows and the next item is ready, process the next ready item
6. Document in PR or notes that the blocked item was skipped and why

## Command Examples

`make queue:validate` (after updating notes), **`make queue:top-item`** (next item as JSON)

## Validation Checklist

- [ ] Blocker documented in queue notes with reason, owner, and next step
- [ ] Item NOT archived (stays in queue.csv)
- [ ] Escalation created (issue or notes)
- [ ] Next ready item identified if processing continues

## Common Failure Modes

Silently skipping blocked item without documenting why → next agent has no context. Fix: always document in notes before moving to next item.

## Handoff Expectations

Queue notes updated with blocked status; escalation created; next agent knows which item is blocked and why.

## Related Procedures

docs/procedures/handle-blocked-work.md

## Related Prompts

prompts/queue_processor.md

## Related Rules

.cursor/rules/queue.md (blocked state rules), AGENTS.md §9 (queue interaction)
