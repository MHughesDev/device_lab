# DeviceLab — Agent Control Plane

Root policy surface for all agents operating in this repository. Read **[README.md](README.md)** first for orientation, then this file completely before touching any code or policy.

---

## 1. Repository mission

DeviceLab is a local-first, BYOC cloud device testing platform. The control plane runs on a developer's laptop. All cloud resources (EC2, Mac Dedicated Host, Device Farm) live in the user's own AWS account. Devices are exposed to AI agents via MCP and to humans via a web UI.

**Stack:** FastAPI + SQLModel + Postgres backend (`apps/api/`) · React 19 + Vite + TanStack frontend (`apps/web/`) · Docker Compose for local dev.

**Primary operators are coding agents.** Humans are reviewers, supervisors, and policy maintainers — not the default execution path.

---

## 2. Instruction hierarchy

When instructions conflict, resolve top-down (higher overrides lower):

1. Explicit task prompt (current run)
2. Root **AGENTS.md** (this file)
3. Scoped **AGENTS.md** files (`apps/api/AGENTS.md`, `apps/web/AGENTS.md`)
4. **`.cursor/rules/`**
5. **`skills/`**
6. **`prompts/`**
7. **`docs/`**

If two sources at the **same rank** disagree — stop and escalate. Do not guess.

---

## 3. Required workflow for every task

1. Read **[README.md](README.md)** — repository map, stack, key resources.
2. Read this file completely.
3. Search **`skills/`** for relevant skills: `make skills:list` or read **`skills/README.md`**; scan *When to invoke*; read every matching skill in full before planning.
4. Read relevant source files and tests.
5. **Plan** — files to touch, acceptance criteria, scope bounds, risks.
6. **Implement** in small validated increments.
7. **Validate** — `make lint`, `make fmt`, `make typecheck`, `make test`.
8. **Update docs** if behavior or operational assumptions changed.
9. **Hand off** — commands run with key output, files changed, PR link, risks, follow-ups.

The skill search in step 3 is non-negotiable for every invocation.

---

## 4. Architecture invariants — never violate

- **Localhost-only control plane.** No inbound ports, no cloud control plane, never expose the API to the internet.
- **BYOC hard boundary.** All cloud resources go in the user's AWS account. DeviceLab never hosts devices.
- **MCP first.** The primary agent interface is MCP; web UI is secondary.
- **No plaintext secrets in model context.** SecretRef indirection always; use `keyring`.
- **Append-only audit log.** HMAC-SHA256 hash chain; never mutate existing entries.
- **Adapter SPI.** Each device family is a versioned plugin; never put device-family-specific logic in the core.

---

## 5. Dependency decisions — locked

Do not swap these without an ADR:

| Concern | Package |
|---------|---------|
| WebRTC | `aiortc` |
| MCP server | `mcp` via FastMCP |
| Browser adapter | `browser-use` |
| Android | `uiautomator2` + `adb` |
| AWS cost | `boto3` + `awspricing` |
| Recipe DSL | `pypyr` |
| Secrets | `keyring` |
| Network proxy | `mitmproxy` |
| AX tree scripts | copy from `viralmind-ai/accessibility-tree-parsers` |
| Audit log | ~100-line HMAC-SHA256 scratch impl |

See `docs/research/notes/oss-repo-candidates.md` for rationale.

---

## 6. Branch and PR policy

| Pattern | Use |
|---------|-----|
| `feat/<short-slug>` | New feature work |
| `fix/<short-slug>` | Bug fixes |
| `claude/<descriptive-slug>-<4-char-suffix>` | Agent-driven work |

- One logical change per PR.
- All CI checks must pass before merge.
- PR descriptions: commands run (with output), files changed, risks.
- No direct push to `main`. No force-push to `main`.
- Delete feature branches after merge.

---

## 7. Planning before coding

Before writing code, produce a plan covering:

- **Acceptance criteria** — exact definition of done.
- **Files** — exhaustive list of files to create or modify.
- **Risks** — security, data integrity, API contract, migration safety.
- **Scope bounds** — what this change explicitly does not do.

Do not start implementation until the plan is written.

---

## 8. Validation before handoff

| Command | Purpose |
|---------|---------|
| `make preflight` | Fast fail-fast checks: format, imports, headers |
| `make lint` | Ruff lint |
| `make fmt` | Apply Ruff formatting |
| `make typecheck` | mypy strict |
| `make test` | Full test suite with coverage |

When to add tests: any behavior change, new endpoint, bug fix, new module.
When to update docs: new env var, new/changed endpoint, behavior change, ops procedure change.

---

## 9. Scope control

- Change only files in scope for the current task.
- Out-of-scope issues: stop, open a GitHub issue, note in the PR — do not fix silently.
- Do not bundle unrelated bug fixes without explicit approval.
- Silent scope creep is a bug in agent behavior. If the same class of mistake repeats, encode a **rule** or **skill** to prevent it.

---

## 10. Escalation of uncertainty

Stop and escalate (do not guess) when:

- Security or data integrity semantics are unclear.
- Spec and code disagree and it is unclear which wins.
- Two instructions at the same rank conflict.
- A required credential or external service is unavailable.

Document in the PR: what is unclear, options, what information is needed, and a recommendation if any.

**Guessing on security or data integrity is forbidden.**

---

## 11. Anti-patterns and forbidden behaviors

- Never commit secrets, credentials, API keys, or tokens.
- Never bypass CI (`--no-verify`), force-push to `main`, or push directly to `main`.
- Never silently expand scope.
- Never run ad hoc shell when a canonical `make` target exists.
- Never use `os.getenv()` outside `apps/api/app/core/config.py` (single Settings object).
- Never add `# type: ignore` without an explanatory comment.
- Never swallow exceptions (`except Exception: pass`).
- Never query the database directly in a router handler.
- Never hardcode environment-specific values in application code.
- Never skip the mandatory skill search before execution.
- Never fix unrelated bugs in the same PR without approval.
- Never put device-family-specific logic in the core — use adapter SPI.
- Never expose plaintext secrets to model context.

---

## 12. When to create or update skills, rules, prompts

| Trigger | Action |
|---------|--------|
| Repeated mistake | Update or add `.cursor/rules/` |
| New recurring workflow | Create or update `skills/` |
| Successful one-off prompt | Promote to `prompts/` |
| Significant architectural decision | Add `docs/adr/` |
| New `make` target | Document in Makefile, README |

---

## 13. Python implementation standards

All Python code follows **[PYTHON_PROCEDURES.md](PYTHON_PROCEDURES.md)** — 18 procedures governing type safety, boundary definitions, import direction, error handling, configuration, async patterns, and testing.

Key rules:
- Every public function is fully typed (params, return, errors).
- Boundary shapes defined as Pydantic models before logic.
- Import direction: `router` → `service` → `repository`. Never reverse.
- No `os.getenv()` outside `apps/api/app/core/config.py`.
- State modeled with `Enum` and explicit transition maps.
- `None` handled explicitly; never used as an error signal.

---

## 14. Navigation

| Area | Location |
|------|----------|
| Authoritative spec | `spec/spec.md` |
| Feature enumeration | `docs/product/end-state-capabilities.md` |
| Roadmap | `docs/roadmap/long-term-plan.md` |
| OSS dependency decisions | `docs/research/notes/oss-repo-candidates.md` |
| API backend | `apps/api/app/` |
| React frontend | `apps/web/src/` |
| Shared contracts | `packages/contracts/` |
| Task interfaces | `packages/tasks/` |
| Compose stack | `compose.yml` + `compose.override.yml` |
| Deploy stubs | `deploy/docker/`, `deploy/k8s/` |
| Documentation | `docs/` — start with `docs/README.md` |
| Skills | `skills/` — `skills/README.md` |
| Prompts | `prompts/` — `prompts/README.md` |
| Scripts | `scripts/` |
| Cursor rules | `.cursor/rules/` |

### Canonical commands

Prefer `make` targets over ad hoc commands. Run `make help` to see all targets.

`make dev`, `make lint`, `make fmt`, `make typecheck`, `make test`, `make migrate`, `make skills:list`, `make prompt:list`

### Handoff format

Include: files changed, commands run with key output, PR link, residual risks, follow-up issues. After PR merge, confirm branch deletion.
