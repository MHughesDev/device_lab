<!-- Generated from: Makefile — do not edit manually -->

## Make targets

| Target | Description |
|--------|-------------|
| `adr-index` | regenerate docs/adr/README.md |
| `audit-self` | repo self-audit |
| `ci-migrate-dry-run` | same SQLite migration checks as CI (preview + apply) |
| `clean` | remove caches and build artifacts |
| `codebase-summary` | regenerate CODEBASE_SUMMARY.md |
| `coverage-ratchet` | compare coverage.xml to policy floor |
| `db-reset` | reset local sqlite + migrate |
| `db-seed` | optional seed data |
| `dev` | Run API with uvicorn --reload (alias for dev-api) |
| `dev-api` | Run API (apps/api) with uvicorn --reload |
| `dev-mcp` | how to run the MicroFast dev MCP server (stdio) |
| `dev-web` | Run frontend (apps/web) dev server via bun |
| `docker-build` | docker compose build |
| `docker-down` | docker compose down |
| `docker-up` | docker compose up -d (uses compose.yml + compose.override.yml) |
| `docs-check` | documentation link check |
| `docs-generate` | placeholder for generated docs |
| `docs-index` | placeholder for docs index |
| `docs-map-check` | verify DOCS_MAP.md and doc_id frontmatter invariants |
| `env-generate` | copy .env.example to .env |
| `env-sync` | compare .env.example with Settings fields (heuristic) |
| `fmt` | Apply Ruff formatting |
| `fmt-check` | Ruff format verify (CI mode) |
| `fmt-fix` | Alias for fmt (apply formatting) |
| `generate-client` | Regenerate openapi TypeScript client in apps/web |
| `health-check` | curl /health |
| `help` | Show targets (see also: scripts/README.md) |
| `image-build` | docker build API image |
| `image-scan` | trivy scan image |
| `init` | pip install -e and .env stub |
| `k8s-render` | kubectl kustomize overlay (OVERLAY=dev|staging|prod) |
| `k8s-validate` | validate kustomize output |
| `lint` | Ruff lint |
| `lint-web` | Run biome lint on apps/web |
| `migrate` | alembic upgrade head |
| `profile-enable` | PROFILE= name |
| `project-health` | aggregate repo health checks for docs-first workflow |
| `prompt-list` | list prompts/*.md |
| `queue-analyze` | validate + analysis stub |
| `queue-archive` | move row to archive (QUEUE_ID= required) |
| `queue-archive-top` | move first open row to archive (no QUEUE_ID — token-friendly) |
| `queue-graph` | mermaid stub / graph placeholder |
| `queue-peek` | show queue header + first row |
| `queue-pr-merge` | after archive+validate — gh pr merge --merge --delete-branch (PR_NUMBER= optional) |
| `queue-top-item` | print first open row as one JSON line (full item for agents) |
| `queue-validate` | validate queue CSV schema |
| `release-prepare` | changelog sanity check |
| `release-verify` | lint + fmt check + typecheck + test |
| `rule-lint` | lint .cursor/rules front matter |
| `rules-check` | cursor rules front matter |
| `scaffold-module` | MODULE= name |
| `secret-scan` | scan for potential secrets (heuristic) |
| `security-scan` | bandit + pip-audit |
| `skill-docs-gen` | run docs-generator.py (regenerate docs/generated) |
| `skills-list` | list skills by folder |
| `test` | pytest with coverage |
| `test-integration` | integration tests only |
| `test-scaffold` | print pytest stubs for a module router (MODULE= required) |
| `test-smoke` | smoke tests only |
| `test-unit` | unit tests only |
| `test-web` | Run frontend playwright tests |
| `typecheck` | mypy strict |
| `web-install` | Install frontend dependencies via bun |
