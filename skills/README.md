# skills/README.md

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: AGENTS.md §13 (Mandatory Skill Search), prompts/skill_searcher.md -->
<!-- - Procedure: docs/procedures/update-or-create-skill.md -->

**Purpose:** Skills decision guide. Start from a task/use-case, then follow the recommended skills.

## How to Use This Index

1. Run `make skills:list` to see this index
2. Identify the PRIMARY domain of your task (backend, security, testing, etc.)
3. Identify any SECONDARY domains (e.g., backend task may also involve testing and security)
4. Read the "When to invoke" section of every relevant skill
5. Read the FULL content of every HIGH-relevance skill before planning or coding
6. Note machinery files (.py alongside .md) as available automation tools

Reference `prompts/skill_searcher.md` for a structured search subroutine.

Skills are execution playbooks, not canonical policy storage. Repository behavior and contribution rules live in `AGENTS.md` and `docs/`.

## Quick task-to-skill guide

- **Initialize repo from IDEA.md** → `skills/init/idea_author.md` (fill IDEA.md), then `skills/init/repo_initialize.md`
- **Implement a queue item end-to-end** → `skills/agent-ops/task-planning.md`, `skills/agent-ops/implementation-handoff.md`, `skills/testing/pytest-conventions.md`
- **Add a new bounded context** → `skills/backend/fastapi-router-module.md`, `skills/backend/service-repository-pattern.md`, `skills/testing/api-contract-testing.md`
- **Add security-sensitive changes** → `skills/security/secret-handling.md`, `skills/security/rbac-tenant-isolation.md`, `skills/security/dependency-review.md`

## Skill Format

Every skill must have: Purpose, When to invoke, Prerequisites, Relevant files/areas, Step-by-step method, Command examples, Validation checklist, Common failure modes, Handoff expectations, Related procedures/prompts/rules.

## Skills by Category

### Initialization (`skills/init/`)
| Skill | When to invoke |
|-------|---------------|
| `idea_author.md` | Turn raw product notes into a complete IDEA.md |
| `repo_initialize.md` | Run after IDEA.md is complete — produces docs, ADRs, MVP queue rows |

### Agent Operations (`skills/agent-ops/`)
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `queue-triage.md` | Read, interpret, and prioritize queue items | `queue-triage.py` |
| `task-planning.md` | Decompose tasks with acceptance criteria and risks | — |
| `implementation-handoff.md` | Write complete handoff documents | `handoff-template-generator.py` |
| `blocked-task-recovery.md` | Handle blocked items without silently skipping | — |
| `prompt-to-procedure-promotion.md` | Promote successful prompts to library | — |
| `rule-refinement-after-mistakes.md` | Encode repeated mistakes as rules | — |
| `post-pr-audit.md` | Audit completed PRs against acceptance criteria | — |
| `repo-self-audit.md` | Run comprehensive repo spec-compliance audit | `repo-self-audit.py` |
| `queue-intelligence.md` | Advanced queue orchestration (DAG, complexity, batches) | `queue-intelligence.py` |

### Repo Governance (`skills/repo-governance/`)
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `writing-agents-md.md` | Author or update AGENTS.md per §4 | — |
| `authoring-cursor-rules.md` | Create or update .cursor/rules/ files | `rule-linter.py` |
| `adding-reusable-commands.md` | Add Make targets or Cursor commands | — |
| `writing-adrs.md` | Author Architecture Decision Records | `adr-index-generator.py` |
| `repository-hygiene.md` | Periodic cleanup: stale branches, orphaned docs | — |
| `docs-generator.md` | Extend and run docs generation pipeline | `docs-generator.py`, `docs-freshness-checker.py` |

### Backend / Platform (`skills/backend/`)
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `fastapi-router-module.md` | Add a new FastAPI router/module | `module-scaffolder.py` |
| `service-repository-pattern.md` | Service and repository layer patterns | — |
| `health-readiness-liveness.md` | Implement and verify health/ready/live endpoints | — |
| `api-versioning.md` | Version API endpoints with URL prefix strategy | — |
| `background-jobs.md` | Define and register background jobs via packages/tasks | — |
| `worker-integration.md` | Enable worker profile with broker connection | — |
| `idempotent-tasks.md` | Design idempotent task handlers | — |
| `configuration-management.md` | Add config via BaseSettings correctly | `env-var-sync.py` |
| `feature-flags.md` | Implement env-based feature flags | — |
| `error-taxonomy.md` | Define and use stable error codes | `error-code-registry.py` |
| `structured-logging.md` | Implement structured JSON logging with correlation IDs | — |
| `opentelemetry-tracing.md` | Add OpenTelemetry tracing | — |
| `metrics-exposition.md` | Expose Prometheus-compatible metrics | — |
| `rate-limiting.md` | Implement rate limiting middleware | — |
| `retries-circuit-breakers.md` | Retry logic and circuit breakers | — |
| `safe-migration-rollout.md` | Roll out migrations safely with expand/contract | — |
| `sqlite-to-postgres.md` | Migrate from SQLite to PostgreSQL | — |

### Security / Compliance (`skills/security/`)
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `secret-handling.md` | Handle secrets: env-only, rotation, detection | `secret-scanner.py` |
| `token-lifecycle.md` | JWT issuance, refresh, revocation, key rotation | — |
| `rbac-tenant-isolation.md` | Verify RBAC and tenant isolation | `tenant-isolation-checker.py` |
| `dependency-review.md` | Review dependency changes for CVEs | `dependency-audit.py` |
| `code-scanning.md` | Run and interpret bandit/semgrep results | — |
| `image-scanning.md` | Scan container images with Trivy | — |
| `sbom-attestation.md` | Generate SBOMs and attestations | — |
| `secure-defaults-review.md` | Audit for secure defaults | — |
| `incident-evidence-capture.md` | Capture evidence during security incidents | — |

### Testing / Quality (`skills/testing/`)
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `pytest-conventions.md` | Pytest conventions, fixtures, markers, coverage | `test-scaffolder.py` |
| `async-testing.md` | Test async FastAPI code with pytest-asyncio | — |
| `api-contract-testing.md` | API contract tests with schema validation | — |
| `snapshot-testing.md` | Snapshot testing for API responses | — |
| `smoke-tests.md` | Write and run smoke tests | — |
| `regression-harness.md` | Add regression tests after bug fixes | — |
| `load-test-basics.md` | Basic load testing with locust/k6 | — |
| `flaky-test-triage.md` | Identify, isolate, and fix flaky tests | `flaky-detector.py` |
| `validation-loop-design.md` | Design validation loops for agent workflows | — |
| `coverage-ratchet.py` | Compare coverage.xml to policy floor | `coverage-ratchet.py` |

### DevOps / Operations (`skills/devops/`)
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `docker-multi-stage-builds.md` | Build efficient multi-stage Docker images | `dockerfile-linter.py` |
| `compose-profiles.md` | Manage Docker Compose profiles | `compose-profile-matrix.py` |
| `k8s-probes.md` | Configure K8s liveness/readiness/startup probes | `k8s-manifest-validator.py` |
| `deploy-to-kubernetes.md` | Deploy to Kubernetes: setup, secrets, DB, troubleshooting | — |
| `rollout-rollback.md` | Kubernetes rollouts and rollbacks | — |
| `github-actions-troubleshooting.md` | Debug failing GitHub Actions | — |
| `release-promotion.md` | Promote releases through dev→staging→prod | — |
| `artifact-publishing.md` | Publish container and Python package artifacts | — |
| `environment-configuration.md` | Manage environment-specific config | — |
| `backup-restore-drills.md` | Backup and restore drills | — |

### AI / RAG (`skills/ai-rag/`) — Optional Profile
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `chromadb-ingestion.md` | Ingest documents into ChromaDB | — |
| `embedding-refresh.md` | Refresh embeddings for updated documents | — |
| `retrieval-evaluation.md` | Evaluate retrieval quality | — |
| `prompt-versioning.md` | Version AI prompts | — |
| `ai-kill-switch.md` | Implement and test AI kill switch | — |
| `model-provider-abstraction.md` | Abstract model/provider dependencies | — |
| `ai-safety-review.md` | Review AI outputs for safety | — |

### Frontend / Mobile (`skills/frontend/`) — Optional Profiles
| Skill | When to invoke | Machinery |
|-------|---------------|-----------|
| `generated-client-usage.md` | Use auto-generated API clients | — |
| `react-api-integration.md` | Integrate React with FastAPI | — |
| `expo-auth-storage.md` | Handle auth tokens in Expo | — |
| `frontend-env-handling.md` | Manage frontend environment variables | — |

## Adding a New Skill

1. Choose the correct category directory
2. Create skill .md with all §6.2 sections
3. Create machinery .py if applicable
4. Update this README index
5. PR with validation (`make rules:check`, `make skills:list`)
