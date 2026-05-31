---
alwaysApply: true
description: Universal constraints applied to every agent interaction in this repository.
---

# .cursor/rules/global.md

Universal constraints for **every** agent session: commits, scope, evidence, file title comments (spec §1.7), mandatory skill search (spec §4.1 item 13), and forbidden patterns. See **[README.md](../../README.md)** (orientation first), **[AGENTS.md](../../AGENTS.md)** (authoritative contract — read at **start of every task** and **again** before merge or when policy is unclear), **[PYTHON_PROCEDURES.md](../../PYTHON_PROCEDURES.md)**, and **`scripts/audit-self.sh`**.

## Mandatory reads (every session)

1. **[README.md](../../README.md)** — repository map, quickstart, essential commands (read before deeper policy and code).
2. **[AGENTS.md](../../AGENTS.md)** — full policy; do not skip. Consult it again before **merge**, **handoff**, or whenever instructions conflict.

## Commit standards

1. Use **Conventional Commits**: `<type>(<scope>): <short description>` with `type` in `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `style`, `perf`, `security`.
2. Subject line **≤ 72** characters.
3. Body explains **why**, not a diff narration; reference queue IDs when applicable (`Closes queue/Q-001`).
4. Never commit with **`--no-verify`** (bypasses hooks).
5. Prefer **one logical change** per commit; squash noise before review.
6. No meaningless subjects (`fix`, `update`, `WIP` without context).

## Scope discipline

1. Edit only files in the **planned scope** for the current task.
2. Out-of-scope findings: **stop**, open a queue row or issue, reference in the PR — do not fix in the same PR without approval.
3. Before editing, confirm the file is in the plan.
4. **"While I'm here"** fixes need explicit approval or a follow-up item.
5. If scope grows by **~20%+**, re-plan and document the expansion.

## Evidence and handoff

1. PR descriptions include: **commands run** (with key output), **files changed**, **tests/docs** updates, **risks**.
2. Queue **notes** (in `queue.csv`) are updated by a **human operator** before archive — implementation agents put PR URL and evidence in the **PR body** and **handoff**; see **`prompts/queue_worker_executor.md`**.
3. If CI fails, paste **failure output** — do not only say "CI failed".
4. After deploy or migration, capture **health check** output when relevant.
5. Architectural decisions need an **ADR** and a link in the PR.

## File title comment standard (spec §1.7)

1. **Python:** first line `# path/from/repo/root/file.py`.
2. **Markdown:** first line `# path/to/file.md` as H1, or `<!-- path/to/file.md -->` when the visible title must differ.
3. **YAML:** first line `# filename.yml` (path or filename).
4. **Shell:** after shebang, `# scripts/name.sh`.
5. **Dockerfile:** first line `# path/to/Dockerfile` (or `# Dockerfile`).
6. **CSV:** `# queue/queue.csv` (or path) **before** the header row.
7. **Batch:** `REM filename.bat`.
8. **JSON:** no comment line (spec waiver).
9. **`scripts/audit-self.sh`** flags files missing title comments (where applicable).
10. No empty files — stubs at least contain the title line.

## Mandatory skill search (spec §4.1 item 13)

**Before any task** (queue, prompt, command, chat, or other):

1. Search **`skills/`** — `make skills:list` or read **`skills/README.md`**.
2. Scan **When to invoke**; read every **relevant** skill **in full** before planning or coding.
3. Note **machinery** (`.py` next to `.md`) as optional automation.
4. For broad tasks, use **`prompts/skill_searcher.md`** as a subroutine.
5. **Do not** start planning or implementation until this step is done.
6. Record which skills you used in the PR (or operator-pasted queue notes).
7. Missing skill for a **recurring** pattern → add or extend a skill (see **`docs/procedures/update-or-create-skill.md`**).

## Semantic discovery of docs (spec §4.1 — see AGENTS.md §16)

**Each turn** (or when the task shifts): use **vector / similarity search**, **@** references, or **natural-language codebase search** to find relevant **skills**, **`docs/procedures/`**, **`prompts/`**, **`docs/`**, and **rules** for the user’s query. Read strong matches. This **adds recall** on top of the skill index; do not rely on grep alone.

## Canonical commands

1. **Always use `make` targets** over ad hoc shell commands. Run `make help` to see all targets.
2. If a `make` target exists for an operation, use it. Do not run the underlying script directly unless debugging the script itself.
3. Colon-form targets (`make queue:validate`) and hyphen-form (`make queue-validate`) are equivalent aliases. Either form is acceptable.
4. If you need a command that has no target, **propose adding one** (new script in `scripts/` + Makefile entry) rather than running a one-off.
5. Document all commands you run in PR descriptions using the Make target form.

## Forbidden patterns

1. No secrets, tokens, passwords, or API keys in the repo.
2. No CI bypass, no direct or force push to **`main`**.
3. No **`os.getenv()`** outside **`apps/api/app/config.py`** (use `Settings` + DI).
4. No bare **`Any`** without a short justification.
5. No **`# type: ignore`** without an explanatory comment.
6. No DB queries in **router** handlers (service/repository only).
7. No hardcoded environment-specific URLs or IDs in application code.
8. No **`except Exception: pass`**.
9. No ad hoc shell when a **`make`** target exists.
10. No skipping the **mandatory skill search** or **semantic discovery** (AGENTS.md §13 and §16).
11. No **`print()`** for production logging (use **`logging`**).
12. No cross-request mutable globals — use request-scoped dependencies.
13. **Queue executor agents** MUST NOT edit **`queue/queue.csv`** or **`queue/queuearchive.csv`** or run **`make queue:archive-top`** / **`make queue:archive`** as part of implementation work — use **`prompts/queue_worker_executor.md`**. Operators own the ledger.
