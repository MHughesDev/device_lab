# skills/repo-governance/architecture-design.md

<!-- CROSS-REFERENCES -->
<!-- - Methodology source: skills/repo-governance/references/tactics-catalog.md -->
<!-- - Methodology source: skills/repo-governance/references/atam-procedure.md -->
<!-- - Methodology source: skills/repo-governance/references/adr-templates.md -->
<!-- - ADR creation: skills/repo-governance/add-adr.md -->
<!-- - Init integration: skills/init/repo_initialize.md (Phase 1 triage uses this skill's Stage 1–2) -->
<!-- - Template: docs/adr/template.md -->
<!-- - Rule: .cursor/rules/documentation.md -->
<!-- - Rule: .cursor/rules/global.md (architectural decisions need ADR + PR link) -->
<!-- - Policy: AGENTS.md §8 -->

**Purpose:** Systematic procedure for reasoning about and deciding software architecture, grounded in the Attribute-Driven Design (ADD) method and Architecture Tradeoff Analysis Method (ATAM). Use this skill whenever a significant architectural decision must be made — during repo initialization, when introducing a new bounded context, evaluating competing implementation approaches, or auditing an existing architecture against quality requirements.

This skill is written for **AI agent execution**, not human team workshops. All stages are internal reasoning the agent performs by reading project documents, not collaborative sessions.

---

## When to Invoke

- `skills/init/repo_initialize.md` Phase 0/1 (triage + spec authoring — that skill calls into Stage 1–2 of this one for any architecturally significant decision)
- A new profile, bounded context, or external integration is being added
- Two or more implementation approaches are viable and the choice has long-term impact
- An existing architecture is being evaluated against a quality attribute it may not satisfy
- Any decision that, if wrong, would require significant rework to reverse

**Do NOT invoke for:**
- Bug fixes or refactoring that preserves observable behavior
- Decisions already made and recorded in `docs/adr/`
- Implementation choices within a single bounded context (those don't need ADD)

---

## Prerequisites

- `IDEA.md` is filled out (or, for non-initialization invocations, the artifact under design is fully described in repo docs).
- The references this skill cites are available: `references/tactics-catalog.md`, `references/atam-procedure.md`, `references/adr-templates.md`.
- The ADR template `docs/adr/template.md` is reachable for Stage 3 recording.
- You can write to `docs/adr/` and have permission to open a PR with the new ADR(s).

---

## Overview: The Three-Stage Pipeline

```
STAGE 1 — READ & EXTRACT     → Gather architecturally significant requirements from IDEA.md
STAGE 2 — DESIGN (ADD loop)  → Iteratively decompose using tactics and patterns
STAGE 3 — RECORD             → Write ADRs; optionally run lightweight ATAM
```

Every stage is mandatory. Do not skip Stage 1 even when requirements seem obvious — a missed quality attribute at this stage is the primary cause of architectural rework.

---

## STAGE 1 — Read the System

Read `IDEA.md` completely before beginning. Extract the four ADD inputs:

### 1A — Functional Requirements

Read `IDEA.md` §2 (problem/solution) and §4.3 (workflows). Identify the **architecturally significant** use cases — those that stress the system, introduce complexity, or constrain structure.

Ask:
- What are the top 5–10 user-facing capabilities?
- Which involve the highest data volume, concurrency, or complexity?
- Are there batch processes, real-time flows, or external integrations?

Discard CRUD-only operations from this list. Only workflows with concurrency, external dependencies, or non-obvious failure modes are architecturally significant.

### 1B — Quality Attribute Scenarios (QAS)

Quality attributes drive architectural decisions more than any functional requirement. For each relevant attribute, construct a **stimulus → response measure** scenario:

| Attribute | Stimulus | Response Measure |
|---|---|---|
| Performance | N concurrent users submit requests | 95th-percentile latency < X ms |
| Availability | Primary database node fails | System recovers within Y seconds, no data loss |
| Modifiability | Add new integration provider | Change confined to 1 module, deployed in < 1 day |
| Security | Unauthenticated request to protected endpoint | 401 returned, attempt logged |
| Scalability | Traffic grows 10× | System scales without re-architecture |

Read `IDEA.md` §13 (constraints), §6 (auth requirements), and §5 (profiles) to populate this table. Then select the **3–5 architectural drivers** — the QAS the architecture *must* satisfy. Everything else is desirable but does not shape structure.

### 1C — Constraints

Read `IDEA.md` §13 explicitly. Collect forced decisions that narrow the design space:
- **Technology**: existing stack, approved languages, mandated cloud provider
- **Organizational**: team size implied by the project scope, skill set assumptions
- **Business**: timeline, compliance requirements (GDPR, HIPAA, SOC2 if mentioned in §13)
- **Existing architecture**: `docs/architecture/` files with `status: current` (components that cannot change)

### 1D — Design Purpose

Classify the current work. This changes how much analysis depth is needed:

| Purpose | When it applies | Depth needed |
|---|---|---|
| **Greenfield** | First initialization from `IDEA.md` | Full ADD loop — all decisions are open |
| **Incremental** | Adding a profile, bounded context, or external integration | ADD loop scoped to the new element only |
| **Evaluation** | Assessing existing architecture against a new QAS | Lightweight ATAM (Stage 3B) |

Document your classification before proceeding to Stage 2.

---

## STAGE 2 — Design (ADD Iteration Loop)

Run this loop once per **iteration**. Each iteration focuses on one system element and produces a set of architectural decisions. For a greenfield initialization, iteration 1 decomposes the entire system. Subsequent iterations decompose each bounded context or profile.

### Step 1 — Set Iteration Scope

State explicitly:
- Which element is being decomposed in this iteration?
- Which QAS from Stage 1B are in scope?
- Which decisions are already locked from prior iterations?

For iteration 1 of a greenfield project: scope is the whole system; all QAS are in scope; no decisions are locked.

### Step 2 — Select Architectural Drivers

From the in-scope QAS, pick the **3–5 that most constrain the design** for this element. These are the drivers. All others are secondary and must not override driver decisions.

### Step 3 — Choose Tactics and Patterns

For each architectural driver, identify candidate **tactics** (design techniques that directly affect a quality attribute) and **patterns** (structural blueprints that compose tactics).

**Quick tactic reference by attribute:**

| Quality Attribute | Primary Tactics |
|---|---|
| Performance | Async processing, caching, connection pooling, read replicas, query optimization |
| Availability | Circuit breaker, retry with backoff, bulkhead isolation, health-based routing |
| Modifiability | Hexagonal / ports-and-adapters, dependency inversion, stable interfaces, feature flags |
| Security | Authenticate at boundary, least-privilege authorization, encrypt in transit and at rest, input validation |
| Scalability | Stateless services, horizontal scaling, queue-based load leveling, DB partitioning |
| Testability | Dependency injection, abstract data sources, limit nondeterminism, test seams |
| Deployability | Immutable infrastructure, feature flags, health checks, rollback capability |

> Full tactic reference: `skills/repo-governance/references/tactics-catalog.md`

**Pattern selection:** for each candidate pattern, score it against each architectural driver (1 = poor fit, 2 = neutral, 3 = strong fit). Select the highest total score, explicitly noting the tradeoffs with second-place options.

| Candidate Pattern | Driver 1 | Driver 2 | Driver 3 | Total | Notes |
|---|---|---|---|---|---|
| Modular monolith | | | | | |
| Microservices | | | | | |
| Event-driven | | | | | |
| Serverless / FaaS | | | | | |

For this repo's default stack (FastAPI, SQLAlchemy, single deployment unit), the **modular monolith** is the baseline unless a QAS explicitly requires independent deployability or polyglot data stores.

### Step 4 — Decompose into Elements

Decompose the chosen element into concrete architectural elements:
- **Name** each element (module, layer, service, adapter)
- **Responsibility**: what does this element own and never delegate?
- **Interfaces**: what does it expose to other elements? What does it consume?
- **QAS addressed**: which architectural driver does this element directly satisfy?

In this repo, elements map to bounded contexts (`apps/api/app/<name>/`) with the standard internal structure: `router.py → service.py → repository.py → models.py`. Dependencies flow inward. The router layer never imports from another router. Cross-context communication uses `packages/contracts/` only.

Document the element decomposition as a list — a prose sketch is sufficient. Mermaid diagrams can be added to `docs/architecture/` docs but are not required at this stage.

### Step 5 — Analyze Against Drivers

For each architectural element, verify the decisions against the architectural drivers:

- Does this structure allow the performance tactic to function? (e.g., can the async task handler actually be decoupled from the request path?)
- Is the modifiability boundary placed at the right seam? (e.g., does the auth adapter isolate the business logic from the JWT library?)
- Does the deployment topology match the availability requirement? (e.g., can the DB failover actually occur without application code changes?)

Classify findings:
- **Non-risk**: the QAS is clearly satisfied — record this and move on
- **Risk**: the current design may fail to satisfy a QAS — document it and propose a mitigation
- **Sensitivity point**: a small change here would significantly affect a quality attribute — mark it
- **Tradeoff point**: this decision improves one QA at the cost of another — record both sides explicitly

### Step 6 — Iterate or Terminate

Check: are all in-scope QAS addressed by at least one architectural decision?
- **Yes** → move to the next unaddressed element (return to Step 1 with narrower scope)
- **No** → return to Step 3 with the new constraints from Step 5 analysis

**Termination condition**: stop when all prioritized QAS have been addressed, or when further decomposition is into implementation detail (single-file scope). Document any unresolved QAS as known risks in the relevant ADR's Consequences section.

---

## STAGE 3 — Record Decisions

Every significant decision from Stage 2 must produce an ADR. Follow `skills/repo-governance/add-adr.md` exactly for the file format, numbering, and validation steps.

**Minimum ADR threshold**: if a decision meets any of the following, write an ADR:
- It selects a pattern, framework, or external service
- It sets a bounded context boundary or communication contract
- It accepts a constraint that limits future options
- It was a close call between two valid approaches

**Not every Stage 2 decision needs an ADR.** Implementation choices within a single bounded context (e.g., which ORM query method to use) do not qualify.

> ADR format reference: `skills/repo-governance/add-adr.md` and `skills/repo-governance/references/adr-templates.md`

### Selecting the Right ADR Format

| Decision Type | Format |
|---|---|
| Standard architectural choice | Extended Nygard (this repo's default — see `docs/adr/template.md`) |
| Multi-option comparison with close scores | MADR variant: add Decision Drivers section and expand Alternatives into a Pros/Cons table per option |
| Platform, cloud, or multi-year commitment | ADD scoring matrix + MADR + lightweight ATAM evaluation (Stage 3B) |
| Replacing a prior decision | Extended Nygard with `**Supersedes:** ADR-NNN` |

### ADR Discipline Rules

- One ADR = one decision. Split if scope creeps beyond a single architectural question.
- Write the ADR **during** the decision, not after implementation — retrospective ADRs lose context.
- Record options considered, not just the option chosen. The rejected options are why the ADR has value.
- Keep status current. When a decision is reversed, mark the old ADR Superseded and link the new one. Never delete ADRs.
- ADRs live in `docs/adr/` co-located with the codebase, not in an external wiki.

---

## STAGE 3B — Lightweight ATAM (for high-stakes decisions)

Run this when a decision is large-scale and hard to reverse, or when a prior analysis flagged risks that need structured evaluation. This is a 1–2 hour internal reasoning process, not a workshop.

> Full 9-step ATAM procedure: `skills/repo-governance/references/atam-procedure.md`

### Phase A — Review Drivers (5 min)

Restate the 3–5 architectural drivers from Stage 1B. Confirm they are still correct given what was learned in Stage 2.

### Phase B — Build Utility Tree (15 min)

Map each architectural driver to a concrete scenario with priority and current satisfaction:

| Scenario (stimulus → response) | Priority | Satisfied? | Evidence |
|---|---|---|---|
| 1,000 concurrent users → p95 < 200ms | H | At Risk | No horizontal scaling path defined |
| DB node failure → recovery < 30s | H | Unknown | Failover not tested |
| Add payment provider → 1 module change | M | Satisfied | Hexagonal pattern in place |

Ratings: Priority = H / M / L (business value). Satisfied = Satisfied / At Risk / Unknown.

Focus all remaining analysis on "At Risk" and "Unknown" scenarios.

### Phase C — Trace and Classify (30 min)

For each "At Risk" or "Unknown" scenario:
1. Which architectural decisions (components, patterns, boundaries) directly affect this scenario?
2. Does the current design satisfy it? What is the evidence or the gap?
3. Classify: Risk / Non-risk / Sensitivity point / Tradeoff point

### Phase D — Identify Risk Themes (15 min)

Group related risks into themes. For each theme, propose at least one mitigation:

| Risk Theme | Risk | Mitigation |
|---|---|---|
| Load handling | No horizontal scaling path | Stateless request handlers + shared session store |
| Failure recovery | DB failover untested | Chaos test in staging; document recovery runbook |

### Phase E — Update ADRs (10 min)

For any architectural decision changed or confirmed by the ATAM analysis, update the corresponding ADR. ATAM findings — especially tradeoff points — are the most valuable content in an ADR's Consequences section.

---

## Output Checklist

After completing all stages, verify before writing any `docs/architecture/` files or application code:

- [ ] All architectural drivers listed with priority and source in `IDEA.md`
- [ ] Pattern selection matrix completed; highest scorer selected with explicit tradeoff note
- [ ] Element decomposition maps every bounded context to a module path
- [ ] Each significant decision has a corresponding ADR in `docs/adr/`
- [ ] Every ADR records options considered, not just the chosen option
- [ ] All risks and tradeoff points documented (informally in the ADR Consequences section is sufficient)
- [ ] Unresolved QAS documented as known risks in the relevant ADR
- [ ] `make adr-index` run after all ADRs written

---

## Integration with Initialize-Repo

When invoked as part of `skills/init/initialize-repo.md`:

- Stage 1 replaces that skill's **Phase 1 — Architectural Reasoning** checklist
- Stage 2 produces the decisions that drive the content of all 25 placeholder docs
- Stage 3 produces `docs/adr/0001-initial-architecture.md` (one ADR file, multiple decision blocks per the init format)
- Stage 3B is optional during init — run it only if two or more patterns scored within 1 point of each other in the Step 3 matrix

The initialize-repo skill's Phase 1 checklist items (bounded context decomposition, entity identification, workflow analysis) are all Stage 1 and Stage 2 outputs. Use this skill to produce them systematically rather than ad hoc.

---

## Reference Files

| File | When to read |
|---|---|
| `skills/repo-governance/references/tactics-catalog.md` | Stage 2 Step 3 — full tactic list per quality attribute |
| `skills/repo-governance/references/atam-procedure.md` | Stage 3B — full 9-step ATAM with utility tree guide |
| `skills/repo-governance/references/adr-templates.md` | Stage 3 — all ADR format variants with annotated examples |
| `skills/repo-governance/add-adr.md` | Stage 3 — step-by-step ADR creation procedure for this repo |
| `docs/adr/template.md` | Stage 3 — this repo's extended Nygard template |

## Related Skills

- `skills/init/initialize-repo.md` — uses this skill for Phase 1 architectural reasoning
- `skills/repo-governance/add-adr.md` — the ADR writing procedure invoked in Stage 3

## Related Rules

- `.cursor/rules/global.md` — architectural decisions require ADR + PR link
- `.cursor/rules/documentation.md` — when ADRs are required
