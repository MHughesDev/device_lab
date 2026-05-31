# skills/agent-ops/post-pr-audit.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedure: docs/procedures/archive-queue-item.md -->
<!-- - Related docs: docs/agents/pr-audit-checklist.md -->

**Purpose:** How to audit a completed PR: verify acceptance criteria met, tests pass, docs updated, queue archived. Per spec §26.4 item 46.

## Purpose

One paragraph. Post-PR audit is the final quality gate after a PR is merged. It verifies that all commitments were fulfilled, the queue item is properly archived, and the handoff is complete. This is distinct from the reviewer's pre-merge review.

## When to Invoke

After a PR is merged (or by a human reviewer). When archiving a queue item post-merge. On periodic audit cadence to check past PRs.

## Prerequisites

PR merged, queue item summary available, CI build results accessible.

## Relevant Files/Areas

queue/queue.csv, queue/queuearchive.csv, docs/agents/pr-audit-checklist.md, the merged PR on GitHub

## Step-by-Step Method

Numbered steps:
1. Read the original queue item summary (acceptance criteria)
2. For each acceptance criterion: verify it is met in the merged code
3. Check that CI passed: lint, typecheck, test, security scan
4. Verify docs were updated if behavior changed (check PR files list for docs/ changes)
5. Verify queue item was archived: check queuearchive.csv for the item ID with status=done
6. Verify handoff was written (PR description should have files changed + commands run)
7. Document any gaps as new queue items

## Command Examples

`make queue:validate` (verify archive is valid), `make test` (re-run to confirm pass)

## Validation Checklist

- [ ] All acceptance criteria met in merged code
- [ ] CI passed (lint, typecheck, test, security)
- [ ] Docs updated if behavior changed
- [ ] Queue item in queuearchive.csv with status=done
- [ ] Handoff document present in PR description
- [ ] Gaps documented as follow-up queue items

## Common Failure Modes

Queue item not archived → next agent thinks it's still open. Fix: always archive with **`make queue:archive-top`** (or **`queue:archive`**) then **`make queue:validate`**; then **`make queue:pr-merge`** (or merge in UI) so GitHub matches the closed item.

## Handoff Expectations

Audit findings documented; any gaps queued; archive entry verified.

## Related Procedures

docs/procedures/archive-queue-item.md, docs/agents/pr-audit-checklist.md

## Related Prompts

prompts/reviewer_critic.md

## Related Rules

.cursor/rules/queue.md (archive-before-delete policy)
