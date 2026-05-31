# .cursor/commands/audit.md

Run the **repository self-audit** before merge or on a schedule.

| Field | Value |
|-------|--------|
| **Name** | Repo self-audit |
| **Description** | Inventory, spec-aligned checks, file title comments, queue schema, docs links — surface **blockers** and **warnings**. |
| **When to use** | Before opening a PR, after large refactors, or periodically. |
| **Prerequisites** | Virtualenv / deps installed per `setup.sh`. |
| **Skill** | [`skills/agent-ops/repo-self-audit.md`](../skills/agent-ops/repo-self-audit.md) |
| **Machinery** | [`skills/agent-ops/repo-self-audit.py`](../skills/agent-ops/repo-self-audit.py) |
| **Make target** | `make audit:self` → `scripts/audit-self.sh` |

## Steps

1. Read [`skills/agent-ops/repo-self-audit.md`](../skills/agent-ops/repo-self-audit.md) and run **mandatory skill search** if this is your first pass today.
2. Run **`make audit:self`** and capture **stdout/stderr**.
3. Classify findings: **BLOCKING** (missing required artifact, broken invariant) vs **WARNING** (style, stale link).
4. Fix **blocking** issues before merge; file issues or queue rows for **warnings** when not immediate.
5. Paste summarized audit evidence into the PR description.

## Typical checks

- Implementation plan / inventory vs disk
- File title comments (spec §1.7) where enforced
- Queue CSV headers and row constraints
- Makefile targets referenced from docs still exist
- Internal doc links not obviously broken (when the script checks them)
