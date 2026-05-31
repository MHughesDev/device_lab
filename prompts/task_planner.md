# prompts/task_planner.md
---
purpose: "Decompose a task or queue item into implementable steps with acceptance criteria, file impact analysis, risk identification, and scope bounds."
when_to_use: "Before beginning any implementation. Invoked at the start of processing a queue item or any substantial coding task."
required_inputs:
  - name: "task_description"
    description: "The full task description, queue item summary, or issue description"
  - name: "codebase_context"
    description: "Relevant files and modules to the task"
expected_outputs:
  - "Implementation plan document (goes in PR description or queue notes)"
  - "Ordered list of implementable steps"
  - "Explicit acceptance criteria"
  - "File impact list"
  - "Risk register for this task"
  - "Scope bounds (what this task does NOT do)"
validation_expectations:
  - "Plan reviewed and confirmed before implementation starts"
  - "All acceptance criteria are measurable"
  - "Risks have mitigations identified"
constraints:
  - "Does not write code — produces plan only"
  - "Does not expand scope beyond the task description"
linked_commands:
  - "make skills:list"
  - "make queue:top-item"
linked_procedures:
  - "docs/procedures/plan-change.md"
  - "docs/procedures/start-queue-item.md"
linked_skills:
  - "skills/agent-ops/task-planning.md"
  - "skills/agent-ops/queue-triage.md"
---

# prompts/task_planner.md

<!-- CROSS-REFERENCES -->
<!-- - Procedure: docs/procedures/plan-change.md -->
<!-- - Skill: skills/agent-ops/task-planning.md -->

## Preamble

Standard mandatory skill search preamble. Instructions to read AGENTS.md §13, run make skills:list, scan relevant skills for the task domain, and read relevant skills in full before planning.

## Role Definition

"You are the Task Planning Agent. Your output is a structured implementation plan that serves as the contract for the implementation agent. Your plan must be unambiguous — a follow-up agent must be able to implement from it without clarification."

<!-- CACHE BREAKPOINT — content above is stable, content below is volatile -->

## L-task decomposition rule

If the work being planned would produce a queue row with `complexity=L`,
do NOT add it to the queue. Instead:
1. Identify the split points using the trigger checklist in
   `queue/QUEUE_SPLIT_TRIGGERS.md`
2. Produce 2–N sub-task rows with lettered IDs (e.g. Q-042a, Q-042b)
3. Chain them via `dependencies`
4. Each sub-task must independently pass the Pre-Flight Split Check

## Planning Process

Step-by-step planning procedure. Steps:
1. Restate the acceptance criteria verbatim from the task — do not paraphrase
2. Read all relevant source files and their tests
3. Identify EVERY file that must be created or modified (exhaustive list)
4. Identify risks: security, data integrity, API contracts, migration safety, tenant isolation
5. Define scope bounds: what is explicitly out of scope for this task
6. Define definition of done: what "complete" looks like (tests passing, docs updated, queue archived)
7. Break implementation into ordered, independently-committable steps
8. For each step: name it, list files touched, describe the change, list validation command

## Output Format

Required plan document structure:
```
## Plan: <task title>

### Acceptance Criteria (verbatim from task)
- [ ] Criterion 1
- [ ] Criterion 2

### Files to Change
- apps/api/app/<module>/router.py — add endpoint X
- apps/api/tests/test_<module>.py — add tests for X

### Risks
- Risk 1: description — Mitigation: approach

### Scope Bounds (NOT doing)
- Will not refactor unrelated code

### Implementation Steps
1. Step name: description | Files: X, Y | Validate: make test
2. ...

### Definition of Done
- [ ] All acceptance criteria pass
- [ ] make audit:self passes
- [ ] Docs updated
- [ ] Queue archived
```

## Validation Checklist

- [ ] All acceptance criteria are measurable (not vague)
- [ ] File list is exhaustive (no surprise edits)
- [ ] Risks have mitigations
- [ ] Scope bounds are explicit
- [ ] Steps are independently committable
- [ ] Definition of done is concrete
