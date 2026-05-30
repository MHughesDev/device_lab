---
doc_id: "5.13"
title: "implement change"
section: "Procedures"
summary: "SOP: Execute code changes in small validated increments with commits that tell a story."
updated: "2026-04-17"
---

# 5.13 — implement change

<!-- CROSS-REFERENCES -->
<!-- - Prompt: prompts/implementation_agent.md -->
<!-- - Validates with: docs/procedures/validate-change.md -->

**Purpose:** SOP: Execute code changes in small validated increments with commits that tell a story. Per spec §26.5 item 141 and §8.3.

## 5.13.1 Purpose

Small increments with validation after each ensures CI is always green, scope is controlled, and the commit history is readable.

## 5.13.2 Trigger / When to Use

After plan-change.md is complete and approved.

## 5.13.3 Prerequisites

Plan document complete. Branch created. Relevant skills read. PYTHON_PROCEDURES.md available for Python-specific patterns.

## 5.13.4 Exact Commands

`make lint`, `make fmt`, `make typecheck`, `make test` (run after each increment)

## 5.13.5 Ordered Steps

The implementation cycle (repeat for each plan step):
1. Read the plan step's target files completely (current state)
2. Implement the specific change for this step only
3. Run `make fmt` — apply formatting
4. Run `make lint` — fix any lint errors before next step
5. Run `make typecheck` — fix any type errors before next step
6. Run `make test` (or targeted: `pytest apps/api/tests/test_<module>.py`) — fix failures
7. Commit with descriptive message: `<type>(<scope>): <description>`
8. Verify commit is self-contained (git show HEAD — no mixed concerns)
9. Proceed to next plan step

## 5.13.6 Expected Artifacts / Outputs

Series of focused commits on the branch. Each commit: single concern, passing lint+typecheck, passing targeted tests. All acceptance criteria met by final commit.

## 5.13.7 Validation Checks

- [ ] Each commit has a descriptive Conventional Commits message
- [ ] No commit contains multiple unrelated changes
- [ ] After each commit: make lint passes, make typecheck passes
- [ ] After last commit: make test passes fully

## 5.13.8 Rollback or Failure Handling

If a step reveals the task is different than planned: stop, re-plan, update queue notes. If a commit introduces a regression: revert with `git revert` (do not amend history after push).

## 5.13.9 Handoff Expectations

All plan steps implemented, commits on branch, make test passes. Ready for validate-change.md.
