# skills/agent-ops/implementation-handoff.md

<!-- CROSS-REFERENCES -->
<!-- - Machinery: skills/agent-ops/handoff-template-generator.py -->
<!-- - Related procedure: docs/procedures/handoff.md -->
<!-- - Related prompt: prompts/implementation_agent.md -->

**Purpose:** [FULL SKILL] How to write a complete handoff document: files changed, commands run with output, risks, follow-ups, PR link, and queue state update. Per spec §26.4 item 42.

## Purpose

One paragraph. A handoff document is the evidence artifact that makes the next agent or human reviewer able to understand exactly what happened, verify the work, assess residual risks, and continue from where this agent stopped. It is non-optional for any meaningful change.

## When to Invoke

- After implementation is complete, before opening PR
- After archiving a queue item
- When handing off to a human reviewer
- When work is blocked and you must stop (partial handoff)

## Prerequisites

- Implementation complete or explicitly blocked
- All validation commands run (make lint, make typecheck, make test, or noting which failed)
- Queue notes (operator updates CSV — executors do not)
- PR opened (or in progress)

## Relevant Files/Areas

- `queue/queue.csv` — notes column (operators only; executors use PR + handoff)
- `queue/queuearchive.csv` — where completed row goes
- `.github/PULL_REQUEST_TEMPLATE.md` — the PR template this populates
- `skills/agent-ops/handoff-template-generator.py` — machinery to auto-populate from git

## Step-by-Step Method

Numbered steps:
1. Run `python skills/agent-ops/handoff-template-generator.py` to generate a pre-populated template
2. Fill out **.github/PULL_REQUEST_TEMPLATE.md** sections:
   - **Summary**: 1-2 sentences of what changed and why
   - **Acceptance Criteria Verification**: per-criterion table (met/not-met/partial with evidence)
   - **Commands Run**: paste output from `make preflight`, `make lint`, `make typecheck`, `make test`
   - **Files Changed**: table with file paths and one-line change descriptions
   - **Residual Risks**: any discovered risks, edge cases
   - **Follow-ups**: out-of-scope items that became new queue rows
3. **PR link**: paste the PR URL
4. **Queue state**: for executors, list operator archive steps per AGENTS.md §9; operators update notes / archive CSV

## Command Examples

- `python skills/agent-ops/handoff-template-generator.py` — generate template
- `git diff --stat HEAD~<n>` — summarize file changes
- `make queue:archive` — archive completed item

## Validation Checklist

- [ ] PR follows `.github/PULL_REQUEST_TEMPLATE.md` structure
- [ ] Summary section captures what and why
- [ ] Acceptance criteria verification table is complete
- [ ] Commands run section has key output for each validation command
- [ ] Files changed table lists all modified files
- [ ] Residual risks documented
- [ ] Follow-up queue items or issues created and referenced
- [ ] PR URL included
- [ ] Queue notes include operator archive steps (executor handoff)

## Common Failure Modes

- **Partial handoff**: listing files but not commands run — reviewer cannot verify. Fix: always include commands + key output.
- **Missing residual risks**: hiding discovered problems. Fix: surface all risks even if they're "probably fine".
- **Queue not updated**: leaving queue row without PR URL → next agent can't find the work. Fix: always update notes before closing.

## Handoff Expectations

The handoff document is a complete audit trail. A human reviewer should be able to: (1) understand what changed, (2) verify it worked (from commands output), (3) know what risks remain, (4) know what follow-up is needed — without talking to the agent.

## Related Procedures

docs/procedures/handoff.md, docs/procedures/archive-queue-item.md

## Related Prompts

prompts/implementation_agent.md, prompts/queue_processor.md

## Related Rules

AGENTS.md §Navigation (handoff format), .cursor/rules/global.md (Evidence requirements)

## Machinery

`skills/agent-ops/handoff-template-generator.py` — reads git diff, recent commands from shell history, queue.csv for current item, and generates a pre-filled Markdown handoff template. Invoke: `python skills/agent-ops/handoff-template-generator.py --queue-id Q-001`
