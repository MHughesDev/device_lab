---
doc_id: "14.2"
title: "documentation freshness"
section: "Repo Governance"
summary: "Keeping docs current — staleness indicators, `make docs:check`, and the quarterly review process."
updated: "2026-04-17"
---

# 14.2 — documentation freshness

<!-- Per spec §20 and §26.5 items 178-182 -->

**Purpose:** Keeping docs current — staleness indicators, `make docs:check`, and the quarterly review process.

## 14.2.1 Why docs go stale

Documentation drifts from reality when:
- A procedure changes but the doc is not updated alongside it.
- A new CI target or Makefile target is added without being mentioned in docs.
- A file is renamed or moved but the docs reference the old path.
- An architectural decision is reversed without updating the ADR.

Stale docs are worse than no docs: they create false confidence and lead agents and engineers to follow incorrect procedures.

## 14.2.2 Staleness indicators

A document is **stale** if any of the following are true:

| Indicator | Signal |
|-----------|--------|
| Links to files that no longer exist | `make docs:check` reports broken paths |
| References a Makefile target that was removed | `grep` for target name in Makefile fails |
| Describes a process that contradicts current CI | CI passes a step the doc says to run manually |
| References an env var not in `.env.example` | Variable is missing or renamed |
| Procedure step references a script that no longer exists | Script path missing from repo |
| Last-modified date > 90 days and the system changed | Quarterly review flag |

## 14.2.3 `make docs:check`

```bash
make docs:check
```

`scripts/docs_check.py` performs:
1. **Broken internal links** — scans every `.md` file for Markdown link syntax with a path in parentheses, resolves relative to repo root, flags 404s.
2. **Orphaned files** — files in `docs/` not linked from any other doc or AGENTS.md (warning, not error).
3. **Missing cross-reference targets** — `<!-- Cross-references -->` blocks reference files that don't exist.
4. **Stale makefile targets** — `## target:` help comments that don't correspond to a real target.

Exit code 0 = no broken links. Exit code 1 = broken links found. CI runs this on every PR.

### Fixing broken links

```bash
make docs:check 2>&1 | grep "BROKEN"
```

Each broken link line shows: `docs/path/to/file.md:42 → target/path.md (NOT FOUND)`. Fix by:
- Updating the link to the new path if the file was moved.
- Removing the link if the referenced file was deleted and its content is no longer relevant.
- Restoring the missing file if it was accidentally deleted.

## 14.2.4 Quarterly review process

At the end of each quarter, the on-call agent or human maintainer performs a **doc freshness audit**:

1. **Run `make docs:check`** and resolve all failures first.
2. **Review the procedures** in `docs/procedures/` against the current Makefile:
   - Does every `make <target>` mentioned in a procedure still exist?
   - Does the procedure's step order match what CI actually does?
3. **Review `docs/security/`** for any expired accepted-risk reviews (see `docs/security/accepted-risks.md`).
4. **Scan for placeholder text** — any doc still containing `TODO`, `TBD`, or `<!--` placeholder comments.
5. **Review REQUIRED_PATHS** in `scripts/repo_self_audit.py` — add any new critical files introduced this quarter.
6. **Update `docs/repo-governance/audits.md`** if new audit checks were added.
7. **Post findings** to the quarterly retrospective (see `docs/repo-governance/improvement-loops.md`).

### Assigning staleness severity

| Severity | Condition | Action |
|----------|-----------|--------|
| **Critical** | Doc describes a security procedure that is now incorrect | Fix within 1 business day; treat as P1 |
| **High** | Doc describes a workflow that now produces errors if followed | Fix before next PR merges in that area |
| **Medium** | Doc references a moved file or renamed target | Fix within current sprint |
| **Low** | Orphaned doc, missing link, or minor wording drift | Fix in next quarterly review |

## 14.2.5 Who owns doc freshness

The author of a change that affects documented behaviour owns updating the docs. This is enforced at PR review time: if a Makefile target changes, the PR reviewer should check that `docs/` references are updated.

The on-call agent is responsible for flagging freshness regressions found during weekly audit checks and adding remediation tasks to `queue/queue.csv`.

## 14.2.6 Adding a new doc

When creating a new `.md` doc under `docs/`:
1. Add the first-line title comment (`# docs/path/to/file.md`) — required by `make audit:self`.
2. Add a `**Purpose:**` line immediately after the title.
3. Link to the new doc from a parent `README.md` or from `AGENTS.md` so it is not orphaned.
4. If the doc describes a procedure, add `make docs:check` to the procedure's validation checklist.
