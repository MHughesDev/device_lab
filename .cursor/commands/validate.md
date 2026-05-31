# .cursor/commands/validate.md

Run the **standard validation suite** before opening a PR.

| Field | Value |
|-------|--------|
| **Name** | Validate |
| **Description** | Lint, format check, typecheck, tests, optional queue/docs/security checks. |
| **When to use** | After substantive edits; before pushing or opening a PR. |
| **Procedure** | [`docs/procedures/validate-change.md`](../docs/procedures/validate-change.md) |

## Steps (Makefile)

Run in order; skip targets that do not exist in this repo yet:

1. **`make fmt`** — Ruff format **check** (CI mode).
2. **`make lint`** — Ruff lint.
3. **`make typecheck`** — mypy strict.
4. **`make test`** — pytest with coverage.
5. **`make queue:validate`** — if **`queue/`** changed.
7. **`make security:scan`** — auth, tenancy, dependency, or security-sensitive changes.

Capture logs and paste key excerpts into the PR.

## Expected output

- Ruff / mypy / pytest **clean** (or only known accepted failures documented).
- Queue validator reports OK when queue files were touched.
- Docs check passes when documentation was edited.
