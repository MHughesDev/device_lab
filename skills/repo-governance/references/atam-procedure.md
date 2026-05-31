# skills/repo-governance/references/atam-procedure.md

**Purpose:** Reference procedure (full and lightweight variants) for the Architecture Tradeoff Analysis Method. Cited by `skills/repo-governance/architecture-design.md` Stage 3 when two design candidates are close enough to require tradeoff analysis. This file is reference material, not an invocable skill on its own.

## When to invoke

- From `skills/repo-governance/architecture-design.md` Stage 3 when two candidate designs scored within 1–2 points and a quantified tradeoff comparison is needed.
- Standalone, when auditing an existing architecture against a quality attribute it may not satisfy.

## Prerequisites

- Stage 1 outputs from `architecture-design.md` are available (quality attribute scenarios, constraints, drivers).
- Two or more candidate designs exist, each with at least a name, sketch, and approximate cost/benefit notes.

## Reference

Full Architecture Tradeoff Analysis Method procedure, plus a lightweight variant for AI agent execution.

Source: Kazman, Klein & Clements — "ATAM: Method for Architecture Evaluation", CMU/SEI Technical Report CMU/SEI-2000-TR-004.

---

## When to Run ATAM

Run the **lightweight variant** (the primary procedure for AI use) when:
- A Stage 2 pattern selection matrix produced two candidates within 1–2 points of each other
- An architectural driver is rated "At Risk" or "Unknown" in the utility tree
- A decision is large-scale and hard to reverse (e.g., database choice, bounded context boundary, async vs. sync processing model)
- A prior ADR is being superseded and the replacement decision needs evaluation

The **full 9-step ATAM** is documented below for completeness but requires a human stakeholder group. For AI-only execution, use the lightweight variant.

---

## Lightweight ATAM for AI Agent Execution

**Input**: Stage 2 outputs — element decomposition, pattern selection, QAS list
**Duration**: one reasoning pass through steps A–F before writing ADRs
**Output**: populated utility tree, risk register, tradeoff map, updated ADR content

### Step A — Restate Drivers

Restate the 3–5 architectural drivers from Stage 1B. Confirm they are still correct given what was learned during Stage 2. If Stage 2 surfaced a constraint that changes which QAS is highest priority, adjust the driver list now.

### Step B — Build Utility Tree

For each architectural driver, write one concrete scenario in stimulus → response form. Rate each:

| Scenario | Priority (H/M/L) | Satisfied? | Evidence or Gap |
|---|---|---|---|
| [stimulus] → [response measure] | | Satisfied / At Risk / Unknown | |

Focus all remaining steps on "At Risk" and "Unknown" rows. Skip "Satisfied" rows unless they introduce a tradeoff.

Priority ratings:
- **H** — business-critical; architecture must satisfy this or the system fails its core purpose
- **M** — important but not blocking; degradation is acceptable temporarily
- **L** — desirable; can be deferred without immediate harm

### Step C — Trace Architecture for Each At-Risk Scenario

For each "At Risk" or "Unknown" row:
1. Name the specific architectural decisions (patterns, boundaries, components) that directly affect this scenario
2. Determine whether the current design satisfies the scenario — state the evidence or the precise gap
3. Classify the finding:

| Classification | Meaning |
|---|---|
| **Risk** | The current decision may fail to satisfy the QAS |
| **Non-risk** | The QAS is clearly satisfied — evidence exists; move on |
| **Sensitivity point** | A small change to this element would significantly affect the quality attribute |
| **Tradeoff point** | This decision improves one QA but weakens another |

### Step D — Identify Risk Themes

Group related risks into themes. For each theme, propose at least one concrete mitigation:

| Risk Theme | Risk | Mitigation | Priority |
|---|---|---|---|
| Load handling | No horizontal scaling path defined | Stateless handlers + external session store | H |
| Failure recovery | DB failover path not defined | Document failover runbook; add health check | H |
| Data isolation | Tenant data query isolation unverified | Row-level `tenant_id` filter in base repository | M |

### Step E — Build Tradeoff Map

For each tradeoff point identified in Step C, document what is improved and what is weakened:

| Decision | Improves | Weakens |
|---|---|---|
| Modular monolith | Operational simplicity, observability | Independent deployability, polyglot flexibility |
| Event-driven async | Scalability, availability | Observability, debugging complexity, consistency |
| Stateless services | Scalability, deployability | Session management complexity |
| Read replicas | Read performance | Eventual consistency on reads |

The tradeoff map is the most actionable ATAM output. Include it in the relevant ADR's Consequences section.

### Step F — Update ADRs

For any architectural decision confirmed, changed, or newly discovered through steps A–E:
- Update the corresponding ADR's Consequences and Risks sections with findings
- If a risk changes the decision itself, supersede the original ADR with a new one
- If risks are accepted, document them explicitly in Consequences → Risks accepted

---

## Risk Register Template

For each risk identified in Step C, record:

```markdown
### Risk R-NN
- **Scenario**: [the QAS that is at risk]
- **Architectural Decision**: [which decision creates this risk]
- **Risk**: [what could go wrong and under what conditions]
- **Probability**: H / M / L
- **Impact**: H / M / L
- **Mitigation**: [proposed action]
- **Status**: Open / In Progress / Mitigated
```

Include this in the relevant ADR's Consequences → Risks accepted section, or in `docs/architecture/overview.md` if it spans multiple contexts.

---

## Full 9-Step ATAM (Reference Only)

The full ATAM requires a human evaluation team and stakeholder group. It is documented here for completeness. AI agents use the lightweight variant above.

### Phase 1 (Day 1 — evaluation team + decision-makers)

**Step 1 — Present the ATAM**: explain the method and expected outputs to all participants.

**Step 2 — Present Business Drivers**: product owner presents functional requirements, quality attribute requirements, constraints, and success criteria.

**Step 3 — Present the Architecture**: architect presents the key design decisions, deployment topology, and known constraints. Participants ask clarifying questions only — no alternatives yet.

**Step 4 — Identify Architectural Approaches**: catalog the patterns and tactics used, per quality attribute.

**Step 5 — Build the Utility Tree**: map each quality attribute to concrete scenarios with priority (H/M/L) and difficulty (H/M/L). H-priority + H-difficulty = critical risk scenario. These drive Step 6.

**Step 6 — Analyze Approaches**: for each high-priority scenario, map it to the architectural decisions that affect it, evaluate whether the current design satisfies it, and classify findings (Risk / Non-risk / Sensitivity point / Tradeoff point).

### Phase 2 (Day 2 — full stakeholder group, 2–3 weeks after Phase 1)

**Step 7 — Brainstorm and Prioritize Scenarios**: stakeholders propose and vote on scenarios. Compare against utility tree; add newly prioritized scenarios to analysis.

**Step 8 — Analyze New Scenarios**: repeat Step 6 for newly added scenarios.

**Step 9 — Present Results**: deliver risk register, tradeoff map, and recommended mitigations to all stakeholders.

### Full ATAM Outputs
1. Risk register (risks + suggested mitigations)
2. Tradeoff map (which decisions conflict across quality attributes)
3. Updated or confirmed architecture with any changes

---

## ATAM Facilitator Notes (for human-run sessions)

- The evaluation team must be independent of the architecture being evaluated. Architects present and clarify, not defend.
- "At Risk" is not a failure — it is the point of the exercise. Encourage candor.
- Risk themes are more useful than individual risks. Group before presenting.
- ATAM does not produce a better architecture — it produces a better-understood one. Redesign is the architect's job after the evaluation.
