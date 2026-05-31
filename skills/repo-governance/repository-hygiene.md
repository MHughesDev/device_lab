# skills/repo-governance/repository-hygiene.md

<!-- CROSS-REFERENCES -->

**Purpose:** Periodic repo cleanup: stale branches, orphaned docs, unused dependencies, dead code detection. Per spec §26.4 item 54.

## Purpose

One paragraph. Repositories accumulate cruft over time: stale branches, orphaned documentation, unused dependencies, dead code paths. Regular hygiene prevents these from becoming noise that degrades agent performance and increases cognitive load for human reviewers.

## When to Invoke

Monthly cadence (create a recurring queue item). After a major release. When repo navigation feels slow or noisy. When CI output has many warnings.

## Prerequisites

Authorized to delete branches. Codebase familiar enough to identify orphaned docs. make audit:self has been run.

## Relevant Files/Areas

All documentation, all Python files, .github/branches (via git branch -r), docs/ directory

## Step-by-Step Method

Numbered steps:
1. **Stale branches**: `git branch -r --merged main` → identify merged branches older than 30 days → delete with approval
2. **Orphaned docs**: run docs-freshness-checker.py → identify docs with no related source changes in 90 days → review and either update or archive
3. **Unused dependencies**: check pyproject.toml against actual imports (`grep -r "import <package>"`) → remove unused deps
4. **Dead code**: identify functions with no callers (tools: vulture or manual grep) → document or remove
5. **Stale prompt templates**: check prompts/README.md → identify templates not used in 90 days → deprecate with note
6. **Queue cleanliness**: run `make queue:validate` → clean up orphaned draft items

## Command Examples

`git branch -r --merged main`, `python skills/repo-governance/docs-freshness-checker.py`, `make queue:validate`

## Validation Checklist

- [ ] Stale branches deleted (with human approval)
- [ ] Orphaned docs reviewed and updated/archived
- [ ] make audit:self passes after cleanup
- [ ] make test passes after any dependency changes

## Common Failure Modes

Deleting a "stale" branch that actually has uncommitted work → data loss. Fix: always check `git log --oneline <branch>` before deleting.

## Handoff Expectations

Hygiene changes committed, audit passing.

## Related Procedures


## Related Prompts

None.

## Related Rules

AGENTS.md §10 (when to update skills/rules/prompts)
