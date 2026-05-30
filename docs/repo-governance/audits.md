---
doc_id: "14.1"
title: "audits"
section: "Repo Governance"
summary: "Scheduled repository self-audits using `make audit:self` — what is checked, how to interpret results, and how to remediate failures."
updated: "2026-04-17"
---

# 14.1 — audits

<!-- Per spec §20 and §26.5 items 178-182 -->

**Purpose:** Scheduled repository self-audits using `make audit:self` — what is checked, how to interpret results, and how to remediate failures.

## 14.1.1 What `make audit:self` checks

The audit script (`scripts/repo_self_audit.py`) runs seven checks and prints a pass/fail report:

| Check | What it validates |
|-------|-------------------|
| `required_files` | All critical repo files exist (AGENTS.md, Dockerfile, queue CSVs, CI workflows, etc.) |
| `queue_validate` | `queue/queue.csv` schema is valid; summaries meet 100-char minimum |
| `file_title_comments` | Every `.py`, `.md`, `.sh`, `.yml` has a first-line title comment per §1.7 |
| `skills_headings` | Every skill `.md` under `skills/` has Purpose, When to invoke, Prerequisites headings |
| `prompts_frontmatter` | Every prompt template has a `---` YAML frontmatter block |
| `prompts_title_and_fields` | Prompt frontmatter contains `purpose:` and `when_to_use:` fields |
| `makefile_help` | Every Makefile target has a `## target: description` help comment |

Exit code 0 = all pass. Exit code 1 = one or more failures. CI blocks on exit code 1.

## 14.1.2 When to run

```bash
make audit:self          # run locally at any time
make audit-self          # hyphen form — identical
```

CI runs `audit-self` as a separate job on every PR and push to main (see `.github/workflows/ci.yml`).

**Trigger manually** before opening a PR if you:
- Added a new script or skill
- Added a Makefile target
- Renamed or moved files

## 14.1.3 How to interpret results

```
# 14.1 — audits

## 14.1.4 required_files: PASS

## 14.1.5 queue_validate: FAIL
  - queue/queue.csv row 3: summary must be empty or >= 100 chars (got 42)

## 14.1.6 file_title_comments: FAIL
  - scripts/new-tool.sh
  - apps/api/app/mymodule/helpers.py
```

Each `FAIL` section lists the offending files or messages. Fix all failures before merging.

## 14.1.7 Remediation guide

### `required_files` failure

A listed file is missing. Either:
- The file was accidentally deleted — restore it from git history (`git checkout HEAD~1 -- <path>`).
- A new required file path needs to be added to `REQUIRED_PATHS` in `scripts/repo_self_audit.py` if the path changed.

### `queue_validate` failure

- **Summary too short:** Expand the queue row summary to be at least 100 characters and descriptive. See `queue/QUEUE_INSTRUCTIONS.md` for the summary writing guide.
- **Header mismatch:** The CSV header was edited — restore it to match `OPEN_HEADER` in `scripts/queue_validate.py`.

### `file_title_comments` failure

Add the file title as the first line:
- Python: `# apps/api/app/module/file.py`
- Shell: Line 1 = `#!/usr/bin/env bash`, Line 2 = `# scripts/my-script.sh`
- Markdown: `# docs/path/to/file.md`
- YAML: Line 1 = `---`, Line 2 = `# .github/workflows/ci.yml` (or file-specific comment)

### `skills_headings` failure

The skill `.md` is missing one or more of: `## Purpose`, `## When to invoke`, `## Prerequisites`. Add the missing headings with content. See `skills/README.md` for the full skill template.

### `prompts_frontmatter` / `prompts_title_and_fields` failure

Prompt templates must begin with `# prompts/<filename>` then a `---` YAML block containing at minimum `purpose:` and `when_to_use:`. See any existing prompt in `prompts/` for the canonical format.

### `makefile_help` failure

Every Makefile target needs a `## target: description` line directly before it:

```makefile
## 14.1.8 my-target: What this target does
my-target:
    @scripts/my-script.sh
```

## 14.1.9 Audit schedule

| Frequency | Who | Scope |
|-----------|-----|-------|
| Every PR | CI (automated) | Full audit — blocks merge on failure |
| Weekly | On-call agent | Review audit trends in CI history |
| Quarterly | Human maintainer | Review REQUIRED_PATHS for completeness; add newly-critical files |

## 14.1.10 Adding new checks

To add a check to the audit:
1. Write a `check_<name>(root: Path) -> list[str]` function in `scripts/repo_self_audit.py` returning a list of violation strings.
2. Add a `sections.append(("<name>", len(violations) == 0, violations))` entry in `main()`.
3. Document the new check in this file.
4. Add a Makefile help comment if exposing as a standalone target.
