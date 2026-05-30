---
doc_id: "5.1"
title: "add make target"
section: "Procedures"
summary: "Standard procedure for adding a new canonical command to the Makefile."
updated: "2026-04-17"
---

# 5.1 — add make target

<!-- CROSS-REFERENCES -->
<!-- - Related skill: skills/repo-governance/adding-reusable-commands.md -->

**Purpose:** Standard procedure for adding a new canonical command to the Makefile.

## 5.1.1 Trigger

When a recurring operation needs a documented, canonical command.

## 5.1.2 Prerequisites

- Understand what the command does.
- Verify no existing target covers this operation (`make help`).

## 5.1.3 Steps

1. Create a shell script in `scripts/<name>.sh` with shebang, `set -euo pipefail`, and file title comment.
2. Make the script executable: `chmod +x scripts/<name>.sh`.
3. Add the target to `Makefile` with a `## name: description` help comment.
4. Add the script to the `.PHONY` declaration.
5. If the target uses colon notation (for example `queue:validate`), add both the hyphen-form primary target and the escaped colon alias (see existing `queue\:validate` patterns).
6. Update `scripts/README.md` with the new script entry.
7. Update `docs/development/local-setup.md` command table if the command is user-facing.
8. Run `make help` to verify the target appears.
9. Run the target to verify it works.

## 5.1.4 Validation

- `make help` shows the new target with description.
- `make <target>` executes successfully.
- `make <target:form>` alias works when applicable.

## 5.1.5 Related

- `skills/repo-governance/adding-reusable-commands.md` — broader guidance for Make targets and Cursor commands.
