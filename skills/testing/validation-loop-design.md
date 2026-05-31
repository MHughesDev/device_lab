# skills/testing/validation-loop-design.md

<!-- CROSS-REFERENCES -->
<!-- - Related rule: .cursor/rules/testing.md -->
<!-- - Related docs: docs/quality/testing-strategy.md -->

**Purpose:** How to design validation loops for agent workflows: what to check, when to check, how to report.

## Purpose

How to design validation loops for agent workflows: what to check, when to check, how to report.

## When to Invoke

- You are adding or changing async tests, HTTP client tests, or pytest-asyncio configuration.
- You are implementing or testing a change that matches the summary above.
- You need a checklist before merging or handing off work in this area.

## Prerequisites

- Read root `AGENTS.md` and complete the mandatory skill search (`make skills-list` or `skills/README.md`).
- Install dev dependencies: `pip install -e ".[dev]"` (or use `./setup.sh`).
- `make test` runs clean locally before you push.

## Relevant Files/Areas

- This skill file and `skills/README.md`
- `docs/procedures/implement-change.md` and `docs/procedures/validate-change.md`
- `apps/api/tests/`
- `pyproject.toml` (pytest / asyncio)
- `docs/quality/testing-strategy.md`

## Step-by-Step Method

1. Read the **Purpose** and **When to Invoke** sections above — confirm this skill applies.
2. Inspect the code and docs listed under **Relevant Files/Areas**.
3. Apply the change in small commits; keep scope aligned with `AGENTS.md` §6.
4. Run `make lint`, `make fmt`, `make typecheck`, and `make test` (add focused pytest if needed).
5. Update user-facing or operator docs if behavior changed.

## Command Examples

- `make lint` — Ruff
- `make fmt` — format check
- `make typecheck` — mypy
- `make test:affected` — pytest with testmon (changed-code only, fast)
- `make test` — full suite (pre-PR gate)
- `pytest apps/api/tests/ -q` — focused run

## Staged Validation Loop

For efficient agent workflows, use a staged validation approach:

1. **Per-increment:** `make test:affected` — validates only code changed since last run (~seconds)
2. **Pre-commit:** `make lint`, `make fmt-check`, `make typecheck` — code quality gates
3. **Pre-PR:** `make test` — full suite with coverage (comprehensive)

This reduces typical validation time from full suite duration to seconds during active development, while maintaining quality guarantees at PR time.

## Validation Checklist

- [ ] Change matches the skill summary and acceptance criteria for the task
- [ ] `make lint`, `make fmt`, `make typecheck`, and `make test` pass
- [ ] Docs or queue notes updated if required by the change

## Common Failure Modes

- **Scope creep**: fix unrelated issues in the same PR — split work per `AGENTS.md` §6.
- **Skipping validation**: run the full `make` checks above before handoff.

## Handoff Expectations

- List files changed, commands run with key output, risks, and follow-ups (see `skills/agent-ops/implementation-handoff.md`).

## Related Procedures

`docs/procedures/implement-change.md`, `docs/procedures/validate-change.md`

## Related Prompts

`prompts/implementation_agent.md`, `prompts/task_planner.md`

## Related Rules

`.cursor/rules/global.md`, `PYTHON_PROCEDURES.md` where applicable
