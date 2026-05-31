# scripts/README.md

<!-- Per spec §26.11 item 255 -->

**Purpose:** Scripts index. Documents each script, its corresponding Make target, and expected behavior. Per spec §26.11 item 255.

## Convention

Every script: `#!/usr/bin/env bash`, `set -euo pipefail`, executable (`chmod +x`). Scripts are the execution layer; Makefile is the interface layer. Never call scripts directly — use `make <target>`.

## Script Index

Table mapping each script to its Make target and purpose:

| Script | Make Target | Purpose |
|--------|------------|---------|
| `dev.sh` | `make dev` | Start local API with hot reload |
| `lint.sh` | `make lint` | Run ruff lint checks |
| `fmt.sh` | `make fmt` | Apply ruff formatting |
| `fmt-check.sh` | `make fmt-check` | Verify ruff formatting (CI) |
| `codebase-summary.sh` | `make codebase-summary` | Manual human/AI-agent refresh of `docs/generated/CODEBASE_SUMMARY.md`; not run by CI |
| `typecheck.sh` | `make typecheck` | Run mypy --strict |
| `preflight.sh` | `make preflight` | Fast fail-fast validation (<10s) |
| `test.sh` | `make test`, `make test:unit`, `make test:integration`, `make test:smoke` | Run test suite |
| `test-affected.sh` | `make test:affected` | Run pytest with testmon (changed-code only) |
| `migrate.sh` | `make migrate`, `make migrate:create` | Database migrations |
| `ci-migrate-dry-run.sh` | `make ci-migrate-dry-run` | SQLite migration preview + apply (parity with CI `migrate-dry-run`) |
| `docs-generate.sh` | `make docs:generate` | Manual human/AI-agent docs generation helper; not run by CI |
| `docs-index.sh` | `make docs:index` | Manual human/AI-agent docs index helper; not run by CI |
| `queue-peek.sh` | `make queue:peek` | Raw CSV: header + first data row |
| `queue-top-item.sh` | `make queue:top-item` | First open row as one JSON line (`queue_top_item.py` → `packages.queue_ops`) |
| `queue-validate.sh` | `make queue:validate` | Validate queue schema |
| `queue-archive.sh` | `make queue:archive`, `make queue:archive-top` | Move row to archive by id, or archive top open row (no id) |
| `queue-pr-merge.sh` | `make queue:pr-merge` | After `queue:archive` + `queue:validate` — `gh pr merge --merge --delete-branch` (optional `PR_NUMBER=`) |
| `queue-metrics.sh` | `make queue:metrics` | Summarize queue audit log metrics |
| `queue-graph.sh` | `make queue:graph` | Render dependency graph |
| `queue-analyze.sh` | `make queue:analyze` | Full queue intelligence analysis |
| `prompt-list.sh` | `make prompt:list` | List prompt templates |
| `skills-list.sh` | `make skills:list` | List skills |
| `rules-check.sh` | `make rules:check` | Validate rule files |
| `audit-self.sh` | `make audit:self` | Repo self-audit |
| `security-scan.sh` | `make security:scan` | Security scanning |
| `image-build.sh` | `make image:build` | Build container image |
| `image-scan.sh` | `make image:scan` | Scan container image |
| `release-prepare.sh` | `make release:prepare` | Prepare release |
| `release-verify.sh` | `make release:verify` | Pre-tag verification |
| `k8s-render.sh` | `make k8s:render` | Render K8s manifests |
| `k8s-validate.sh` | `make k8s:validate` | Validate manifests |
| `clean.sh` | `make clean` | Remove build artifacts |
| `db-reset.sh` | `make db:reset` | Drop/recreate local DB |
| `seed-db.sh` | `make db:seed` | Seed sample data |
| `health-check.sh` | `make health:check` | Check API health |
| `init-repo.sh` | `make init` | Initialization pre-checks |
| `scaffold-module.sh` | `make scaffold:module` | Scaffold domain module |
| `profile-enable.sh` | `make profile:enable` | Enable optional profile |
| `generate-env.sh` | `make env:generate` | Generate .env |
| `queue_top_item.py` | (via `queue-top-item.sh`) | First open row as JSON (`packages.queue_ops`) |
| `queue_validate.py` | (via `queue-validate.sh`) | CSV schema validation (`packages.queue_ops`) |
| `queue_archive.py` | (via `queue-archive.sh`) | Move queue row to archive |
| `repo_self_audit.py` | (via `audit-self.sh`) | Lightweight audit runner |
| `rename-from-template.py` | direct script | Rename README, AGENTS.md mission fields, package metadata, and `pyproject.toml` for a new product |
| `template_token_sweep.py` | direct script | Report residual template tokens with file:line suggestions for a product name |

Skill machinery (invoked via Make, not shell wrappers):

| Skill | Make Target |
|-------|-------------|
| `skills/security/secret-scanner.py` | `make secret-scan` / `make secret:scan` |
| `skills/testing/test-scaffolder.py` | `make test-scaffold MODULE=…` |
| `skills/backend/env-var-sync.py` | `make env-sync` |
| `skills/testing/coverage-ratchet.py` | `make coverage-ratchet` |
| `skills/repo-governance/rule-linter.py` | `make rule-lint` |
| `skills/repo-governance/adr-index-generator.py` | `make adr-index` |
