# Makefile
# Canonical command entrypoint. Prefer `make <target>` over ad hoc shell.

SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

.PHONY: help dev dev-api dev-web lint lint-web fmt fmt-check fmt-fix typecheck test test-web test-unit test-integration test-smoke \
        migrate migrate\:create ci-migrate-dry-run db-reset db-seed docs-generate docs-index hooks-install \
        queue-peek queue-top-item queue-validate queue-archive queue-archive-top queue-pr-merge queue-graph queue-analyze queue-metrics \
        prompt-list skills-list rules-check audit-self \
        security-scan secret-scan image-build image-scan \
        release-prepare release-verify \
        k8s-render k8s-validate docker-up docker-down \
        init \
        scaffold-module profile-enable env-generate \
        codebase-summary skill-docs-gen \
        test-scaffold env-sync coverage-ratchet rule-lint adr-index \
        web-install generate-client \
        clean health-check project-health \
        hooks-install

## help: Show targets (see also: scripts/README.md)
help:
	@echo "Targets:"
	@grep -E '^##' $(MAKEFILE_LIST) | sed 's/^## //' | column -t -s ':'

## dev: Run API with uvicorn --reload (alias for dev-api)
dev: dev-api

## dev-api: Run API (apps/api) with uvicorn --reload
dev-api:
	@scripts/dev.sh

## dev-web: Run frontend (apps/web) dev server via bun
dev-web:
	@cd apps/web && bun run dev

## web-install: Install frontend dependencies via bun
web-install:
	@cd apps/web && bun install

## lint-web: Run biome lint on apps/web
lint-web:
	@cd apps/web && bun run lint

## test-web: Run frontend playwright tests
test-web:
	@cd apps/web && bun run test

## generate-client: Regenerate openapi TypeScript client in apps/web
generate-client:
	@cd apps/web && bun run generate-client

## lint: Ruff lint
lint:
	@scripts/lint.sh

## fmt: Apply Ruff formatting
fmt:
	@scripts/fmt.sh

## fmt-check: Ruff format verify (CI mode)
fmt-check:
	@scripts/fmt-check.sh

## fmt-fix: Alias for fmt (apply formatting)
fmt-fix: fmt

## typecheck: mypy strict
typecheck:
	@scripts/typecheck.sh

## test: pytest with coverage
test:
	@scripts/test.sh

## test-unit: unit tests only
test-unit:
	@TEST_TYPE=unit scripts/test.sh

## test-integration: integration tests only
test-integration:
	@TEST_TYPE=integration scripts/test.sh

## test-smoke: smoke tests only
test-smoke:
	@TEST_TYPE=smoke scripts/test.sh

## test-affected: pytest with testmon (changed-code only)
test-affected:
	@scripts/test-affected.sh

## preflight: fast deterministic checks (<10s fail-fast)
preflight:
	@scripts/preflight.sh

## migrate: alembic upgrade head
migrate:
	@scripts/migrate.sh

## migrate\:create: alembic revision --autogenerate (MESSAGE= required)
migrate\:create:
	@MESSAGE="$(MESSAGE)" scripts/migrate.sh create

## ci-migrate-dry-run: same SQLite migration checks as CI (preview + apply)
ci-migrate-dry-run:
	@scripts/ci-migrate-dry-run.sh

## db-reset: reset local sqlite + migrate
db-reset:
	@scripts/db-reset.sh

## db-seed: optional seed data
db-seed:
	@scripts/seed-db.sh


## docs-generate: manual human/AI-agent docs generation (not CI)
docs-generate:
	@scripts/docs-generate.sh

## docs-index: manual human/AI-agent docs index helper (not CI)
docs-index:
	@scripts/docs-index.sh

## queue-peek: show queue header + first row
queue-peek:
	@scripts/queue-peek.sh

## queue-top-item: print first open row as one JSON line (full item for agents)
queue-top-item:
	@scripts/queue-top-item.sh

## queue-validate: validate queue CSV schema
queue-validate:
	@scripts/queue-validate.sh

## queue-archive: move row to archive (QUEUE_ID= required)
queue-archive:
	@QUEUE_ID="$(QUEUE_ID)" scripts/queue-archive.sh

## queue-archive-top: move first open row to archive (no QUEUE_ID — token-friendly)
queue-archive-top:
	@ARCHIVE_TOP=1 scripts/queue-archive.sh

## queue-pr-merge: after archive+validate — gh pr merge --merge --delete-branch (PR_NUMBER= optional)
queue-pr-merge:
	@PR_NUMBER="$(PR_NUMBER)" scripts/queue-pr-merge.sh

## queue-graph: mermaid stub / graph placeholder
queue-graph:
	@scripts/queue-graph.sh

## queue-analyze: validate + analysis stub
queue-analyze:
	@scripts/queue-analyze.sh

## queue-metrics: summarize audit.log metrics
queue-metrics:
	@scripts/queue-metrics.sh

## prompt-list: list prompts/*.md
prompt-list:
	@scripts/prompt-list.sh

## skills-list: list skills by folder
skills-list:
	@scripts/skills-list.sh

## rules-check: cursor rules front matter
rules-check:
	@scripts/rules-check.sh

## audit-self: repo self-audit
audit-self:
	@scripts/audit-self.sh

## security-scan: bandit + pip-audit
security-scan:
	@scripts/security-scan.sh

## image-build: docker build API image
image-build:
	@scripts/image-build.sh

## image-scan: trivy scan image
image-scan:
	@scripts/image-scan.sh

## release-prepare: changelog sanity check
release-prepare:
	@scripts/release-prepare.sh

## release-verify: lint + fmt check + typecheck + test
release-verify:
	@scripts/release-verify.sh

## k8s-render: kubectl kustomize overlay (OVERLAY=dev|staging|prod)
k8s-render:
	@OVERLAY="$(or $(OVERLAY),dev)" scripts/k8s-render.sh

## k8s-validate: validate kustomize output
k8s-validate:
	@OVERLAY="$(or $(OVERLAY),dev)" scripts/k8s-validate.sh

## docker-up: docker compose up -d (uses compose.yml + compose.override.yml)
docker-up:
	docker compose up -d

## docker-down: docker compose down
docker-down:
	docker compose down

## docker-build: docker compose build
docker-build:
	docker compose build

## init: pip install -e and .env stub
init:
	@scripts/init-repo.sh

## hooks-install: install pre-commit hooks (run once after cloning)
hooks-install:
	@scripts/install-hooks.sh

## scaffold-module: MODULE= name
scaffold-module:
	@MODULE="$(MODULE)" scripts/scaffold-module.sh

## profile-enable: PROFILE= name
profile-enable:
	@PROFILE="$(PROFILE)" scripts/profile-enable.sh

## env-generate: copy .env.example to .env
env-generate:
	@scripts/generate-env.sh

## codebase-summary: manual human/AI-agent docs/generated/CODEBASE_SUMMARY.md refresh
codebase-summary:
	@scripts/codebase-summary.sh

## skill-docs-gen: manual human/AI-agent docs-generator.py run (not CI)
skill-docs-gen:
	@python3 skills/repo-governance/docs-generator.py --mode generate --repo-root .

## secret-scan: scan for potential secrets (heuristic)
secret-scan:
	@python3 skills/security/secret-scanner.py --repo-root .

## test-scaffold: print pytest stubs for a module router (MODULE= required)
test-scaffold:
	@python3 skills/testing/test-scaffolder.py --repo-root . --module "$(MODULE)"

## env-sync: compare .env.example with Settings fields (heuristic)
env-sync:
	@python3 skills/backend/env-var-sync.py --repo-root .

## coverage-ratchet: compare coverage.xml to policy floor
coverage-ratchet:
	@python3 skills/testing/coverage-ratchet.py --repo-root .

## rule-lint: lint .cursor/rules front matter
rule-lint:
	@python3 skills/repo-governance/rule-linter.py --repo-root .

## adr-index: regenerate docs/adr/README.md
adr-index:
	@python3 skills/repo-governance/adr-index-generator.py --repo-root .

## clean: remove caches and build artifacts
clean:
	@scripts/clean.sh

## health-check: curl /health
health-check:
	@scripts/health-check.sh

## project-health: aggregate repo health checks for docs-first workflow
project-health:
	@scripts/project-health.sh

# --- Colon-style aliases (spec §10.2 and docs). GNU Make needs escaped colons in target names.
.PHONY: skills\:list queue\:peek queue\:top-item queue\:validate queue\:archive queue\:archive-top queue\:pr-merge queue\:graph queue\:analyze queue\:metrics audit\:self rules\:check \
        docs\:check docs\:generate docs\:index security\:scan release\:prepare release\:verify docker\:up docker\:down \
        health\:check project\:health profile\:enable \
        scaffold\:module test\:unit test\:integration \
        test\:smoke test\:affected preflight fmt\:fix fmt\:check prompt\:list db\:reset db\:seed ci\:migrate-dry-run image\:build image\:scan \
        k8s\:render k8s\:validate env\:generate skill\:docs-gen \
        secret\:scan test\:scaffold env\:sync coverage\:ratchet rule\:lint adr\:index

skills\:list: skills-list
queue\:peek: queue-peek
queue\:top-item: queue-top-item
queue\:validate: queue-validate
queue\:archive: queue-archive
queue\:archive-top: queue-archive-top
queue\:pr-merge: queue-pr-merge
queue\:graph: queue-graph
queue\:analyze: queue-analyze
queue\:metrics: queue-metrics
audit\:self: audit-self
rules\:check: rules-check
docs\:generate: docs-generate
docs\:index: docs-index
security\:scan: security-scan
release\:prepare: release-prepare
release\:verify: release-verify
docker\:up: docker-up
docker\:down: docker-down
health\:check: health-check
profile\:enable: profile-enable
scaffold\:module: scaffold-module
test\:unit: test-unit
test\:integration: test-integration
test\:smoke: test-smoke
test\:affected: test-affected
preflight: preflight
fmt\:fix: fmt-fix
fmt\:check: fmt-check
prompt\:list: prompt-list
db\:reset: db-reset
db\:seed: db-seed
ci\:migrate-dry-run: ci-migrate-dry-run
image\:build: image-build
image\:scan: image-scan
k8s\:render: k8s-render
k8s\:validate: k8s-validate
env\:generate: env-generate
skill\:docs-gen: skill-docs-gen
secret\:scan: secret-scan
test\:scaffold: test-scaffold
env\:sync: env-sync
coverage\:ratchet: coverage-ratchet
rule\:lint: rule-lint
adr\:index: adr-index

project\:health: project-health
hooks\:install: hooks-install
