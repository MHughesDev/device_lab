# skills/devops/artifact-publishing.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedures: docs/operations/ -->

**Purpose:** How to publish build artifacts: container registry push, Python package publishing, artifact retention.

## Purpose

How to publish build artifacts: container registry push, Python package publishing, artifact retention.

## When to Invoke

- You are changing Docker, Kubernetes, CI workflows, or release automation.
- You are implementing or testing a change that matches the summary above.
- You need a checklist before merging or handing off work in this area.

## Prerequisites

- Read root `AGENTS.md` and complete the mandatory skill search (`make skills-list` or `skills/README.md`).
- Install dev dependencies: `pip install -e ".[dev]"` (or use `./setup.sh`).
- Docker and/or `kubectl` available if you touch deploy manifests.

## Relevant Files/Areas

- This skill file and `skills/README.md`
- `docs/procedures/implement-change.md` and `docs/procedures/validate-change.md`
- `deploy/docker/`
- `deploy/k8s/`
- `.github/workflows/`

## Step-by-Step Method

1. Read the **Purpose** and **When to Invoke** sections above — confirm this skill applies.
2. Inspect the code and docs listed under **Relevant Files/Areas**.
3. Apply the change in small commits; keep scope aligned with `AGENTS.md` §6.
4. Run `make lint`, `make fmt`, `make typecheck`, and `make test` (add focused pytest if needed).
4b. Run `make k8s-validate` or `make image-build` when deploy artifacts change.
5. Update user-facing or operator docs if behavior changed.

## Command Examples

- `make lint` — Ruff
- `make fmt` — format check
- `make typecheck` — mypy
- `make test` — full suite
- `make docker-up` / `make docker-down`
- `make k8s-validate`

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
