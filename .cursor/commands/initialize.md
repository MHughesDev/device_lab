# .cursor/commands/initialize.md

Run repository initialization from a fully completed **`IDEA.md`** via the single canonical initialization skill.

| Field | Value |
|-------|--------|
| **Name** | Initialize repository |
| **Description** | Read a completed **`IDEA.md`**, refresh the spec and design docs, and seed initial MVP queue rows. Do not write product code. |
| **When to use** | A new project after the developer has filled out **`IDEA.md`** end-to-end. |
| **Prerequisites** | Python 3.12+, Docker, Make; **`IDEA.md`** completed (every applicable section filled, `N/A` where inapplicable). |
| **Primary prompt** | [`prompts/repo_initializer.md`](../prompts/repo_initializer.md) |
| **Canonical skill** | [`skills/init/repo_initialize.md`](../skills/init/repo_initialize.md) |
| **Procedure** | [`docs/procedures/initialize-repo.md`](../docs/procedures/initialize-repo.md) |

## Steps

1. Read this command and **[AGENTS.md](../AGENTS.md)** — run **mandatory skill search** before any edits.
2. Open and read [`prompts/repo_initializer.md`](../prompts/repo_initializer.md) end-to-end.
3. Read **`IDEA.md`** completely. If any applicable section is blank or any open question would change MVP architecture, stop and surface those gaps to the developer — do not invent answers.
4. Run [`skills/init/repo_initialize.md`](../skills/init/repo_initialize.md) end-to-end (six phases: triage → spec → docs → ADR → MVP queue → validate).
6. Open **one** PR titled `init: <product name>` summarizing what was initialized and what remains blocked.

## Expected output

- Initialization **PR** with green CI.
- Refreshed design docs under `docs/`.
- `queue/queue.csv` seeded with MVP rows walking from the baseline to the MVP defined in `IDEA.md §4`.
- Blocked `category=human-ops` rows for unresolved `IDEA.md §19` open questions.
