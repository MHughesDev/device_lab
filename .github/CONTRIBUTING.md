# Contributing to DeviceLab

## How work is organized

All planned work lives in `queue/queue.csv`. Before writing any code, there must be a queue row with clear acceptance criteria. See `queue/QUEUE_INSTRUCTIONS.md` for the full system.

## Workflow

1. **Find or create a queue row.** Check `queue/queue.csv` for existing rows covering your change. If none exists, open a Queue Row Request issue or add a row following `QUEUE_INSTRUCTIONS.md`.

2. **Create a branch.** Name it after the queue row: `feat/Q-101-local-foundation`.

3. **Read before writing.** Read every file listed in the row's `context_files` before making changes. Read `AGENTS.md` §5 for implementation conventions.

4. **Stay in scope.** Only modify files listed in the row's `touch_files`. If you discover you need to touch more, note it in the PR and create follow-up queue rows.

5. **Open a PR.** Use the PR template — it asks for the queue row ID and acceptance criteria verbatim. Reviewers verify against those criteria, not a vague description.

6. **Archive on merge.** When a PR merges, the queue row moves from `queue/queue.csv` to `queue/queuearchive.csv` with status `done`.

## Validation commands

```bash
# Queue integrity
python scripts/queue_validate.py

# Docs map check
python scripts/check_docs_map.py

# Self-audit
python scripts/repo_self_audit.py

# Full test suite (once code exists)
make test
```

## Commit style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(Q-101): stand up localhost control plane defaults
fix(Q-103): correct wizard redirect after preflight failure
docs(Q-100): replace init-manifest stub with repo_initialize artifacts
```

## Scope rules

- Do not touch files outside your queue row's `touch_files` without explicit justification in the PR.
- Do not add features, refactors, or cleanup beyond the queue row's acceptance criteria.
- Do not commit secrets, `.env` files, or credentials under any circumstances.

## Questions

Open an issue or check `docs/open-questions.md` for known unresolved decisions.
