# CONTRIBUTING.md

How to contribute to this repository — for **humans** and **agents**. Agent policy lives in **[AGENTS.md](AGENTS.md)**; this file complements it with contribution mechanics.

## How to contribute

This repository is designed for **coding agents** as primary operators. Humans contribute by maintaining **policy** (AGENTS.md, rules, skills, procedures, CI), reviewing **PRs**, filling **`IDEA.md`** for initialization, and steering the queue.

**Start here:** [AGENTS.md](AGENTS.md) — instruction hierarchy, mandatory skill search, validation, and queue rules.

**Agent tooling:** This repo does **not** require connecting a template-specific MCP server. Use **`make queue:top-item`** / **`python scripts/queue_top_item.py`** and **`packages/queue_ops`** for queue I/O; see **[docs/development/local-setup.md](docs/development/local-setup.md)** (*Agent and queue tooling*).

## Development setup

1. Clone the repository.
2. Run **`./setup.sh`** (Linux/macOS/WSL/Git Bash on Windows) for a guided bootstrap, **or** follow **[docs/development/local-setup.md](docs/development/local-setup.md)**.
   - **Note for Windows users:** The template standardizes on WSL or Git Bash. `setup.bat` is not provided.
3. Use **`make dev`** for the local stack and **`make test`** to verify.

Full prerequisites: **[docs/getting-started/](docs/getting-started/)**.

## Branch naming

| Pattern | When |
|---------|------|
| `queue/<id>-short-slug` | Queue-driven work — **include the queue item ID** |
| `cursor/<descriptive-slug>-<4-char-suffix>` | Agent/Cursor work not from a queue row |
| `hotfix/<description>` | Urgent human-initiated fixes (use sparingly) |

Branches that do not match an agreed pattern may be rejected at review.

## Pull requests

1. Open a PR against **`main`** (no direct pushes to `main`).
2. Use **`.github/PULL_REQUEST_TEMPLATE.md`** for the description.
3. Keep **one logical change** per PR when practical.
4. Ensure **CI is green** (lint, format check, typecheck, tests, and any other required checks).
5. Include **evidence**: queue ID if applicable, files touched, commands run with output, tests and docs updated, risks called out.

Step-by-step: **[docs/procedures/open-pull-request.md](docs/procedures/open-pull-request.md)**.

## Queue-driven work

The CSV queue is **agent work orchestration**, not a product backlog.

- **`queue/queue.csv`** — open items; the **top data row** is the active item in single-lane mode.
- Branch as **`queue/<id>-slug`**, implement, validate, then **archive** per SOP.

Read **[queue/QUEUE_INSTRUCTIONS.md](queue/QUEUE_INSTRUCTIONS.md)**. Related procedures: **[docs/procedures/start-queue-item.md](docs/procedures/start-queue-item.md)**, **[docs/procedures/archive-queue-item.md](docs/procedures/archive-queue-item.md)**.

Adding rows to the queue is how maintainers **direct agent work** in an auditable way.

## Code of conduct

This project follows **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** when present. Otherwise: be respectful, assume good intent, and keep review feedback actionable.

## Questions and escalation

| Topic | Where |
|-------|--------|
| Spec / policy | GitHub issue, or ask in PR with context |
| Blocked queue work | **[docs/procedures/handle-blocked-work.md](docs/procedures/handle-blocked-work.md)** |
| Security | **[SECURITY.md](SECURITY.md)** — do not file public issues for undisclosed vulnerabilities |
| Architecture | Discussion, ADR under **`docs/adr/`**, or design PR |
