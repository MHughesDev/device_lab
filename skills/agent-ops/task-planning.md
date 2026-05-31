# skills/agent-ops/task-planning.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedure: docs/procedures/plan-change.md -->
<!-- - Related prompt: prompts/task_planner.md -->

**Purpose:** [FULL SKILL] How to decompose a task into implementable steps with acceptance criteria, file impact analysis, risk identification, and scope bounds. Per spec §26.4 item 41.

## Purpose

One paragraph. This skill produces an implementation plan document that is the contract between planning and implementation. A plan reduces implementation errors by explicitly stating: what must be true when done, which files will change, what risks exist, and what is explicitly out of scope.

## When to Invoke

- Before beginning any implementation (mandatory)
- After reading a queue item but before branching
- When a task is discovered to be larger than expected (re-plan)
- After a blocking issue is resolved and work resumes

## Prerequisites

- Task description or queue item fully read
- Mandatory skill search completed (AGENTS.md §13)
- Relevant source files read
- AGENTS.md §5 (Planning before coding) reviewed

## Relevant Files/Areas

- The source files that will change
- `apps/api/app/` — API source modules
- `apps/api/tests/` — test files
- `docs/procedures/plan-change.md` — the SOP this skill implements

## Step-by-Step Method

Numbered steps:
1. Restate acceptance criteria VERBATIM from the queue item or task — do not paraphrase
2. Read the current implementation of every file in the affected area
3. List every file that must be created or modified (exhaustive — no surprises)
4. For each file: describe the specific change (add function X, modify class Y, add endpoint Z)
5. Identify risks: security (auth, tenant), data integrity (migration), API contract (breaking change), test coverage
6. For each risk: state the mitigation approach
7. Define explicit scope bounds: list 3-5 things this task explicitly does NOT do
8. Write the definition of done: what "complete" looks like verifiably
9. Break implementation into ordered, independently-committable steps
10. Estimate validation commands after each step
11. Write the plan in the format below

## Command Examples

- **`make queue:top-item`** — full top row as one JSON line
- `make skills:list` — check for relevant skills
- (No other commands — planning is a read+write-document activity)

## Validation Checklist

- [ ] Acceptance criteria verbatim from task (no paraphrasing)
- [ ] File list is exhaustive
- [ ] Each file has a specific change description
- [ ] Risks identified with mitigations
- [ ] Scope bounds explicit (at least 3 non-goals listed)
- [ ] Definition of done is concrete and verifiable
- [ ] Steps are independently committable
- [ ] Plan reviewed before implementation starts

## Common Failure Modes

- **Vague acceptance criteria**: "implement the feature" — impossible to verify. Fix: always quote verbatim from the task summary.
- **Missing files in list**: discovering unplanned files during implementation. Fix: read all related code before planning, not during.
- **No scope bounds**: scope creep during implementation. Fix: explicitly list 3-5 non-goals.
- **Missing risk**: discovering a security risk after implementation. Fix: always check security/tenancy risks explicitly.

## Handoff Expectations

The plan document is handed to the implementation agent. It must be:
- Stored in PR description draft or queue notes
- Complete enough that a different agent could implement from it without clarification
- Linked from the queue item notes when queue-driven

## Related Procedures

docs/procedures/plan-change.md

## Related Prompts

prompts/task_planner.md, prompts/implementation_agent.md

## Related Rules

AGENTS.md §5 (Planning before coding), .cursor/rules/global.md (Scope discipline)
