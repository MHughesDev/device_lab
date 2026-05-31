# skills/repo-governance/references/adr-templates.md

**Purpose:** Reference catalog of ADR format variants with annotated examples. Used as a lookup table by `skills/repo-governance/architecture-design.md` (Stage 3) and `skills/repo-governance/add-adr.md`. This file is reference material, not an invocable skill — the surrounding skills cite specific sections of it as needed.

## When to invoke

- Indirectly, from `skills/repo-governance/architecture-design.md` Stage 3 when recording a decision and the default Extended Nygard format is not the obvious fit.
- Indirectly, from `skills/repo-governance/add-adr.md` when selecting an ADR format for a new record.
- Read this file directly when you need to compare formats or read a worked example before authoring.

## Prerequisites

- You are about to write an ADR under `docs/adr/` and have already read `docs/adr/template.md` (the repo's default format).
- You have a candidate decision in mind with context, alternatives, and at least a working draft of consequences.

## Reference

All major ADR format variants with annotated examples. Use this alongside `skills/repo-governance/add-adr.md` when choosing which format to apply.

This repo's **default format** is the extended Nygard (Template 1). Use other formats when the decision type warrants it — see the selection guide in `add-adr.md`.

Sources: MADR 4.0 (adr.github.io/madr), Nygard (cognitect.com/blog/2011), Y-statements (Zimmermann / InfoQ 2015), Tyree-Ackerman (Capital One / IEEE Software 2005).

---

## Template 1 — Extended Nygard (This Repo's Default)

**Use when**: any significant architectural decision. This is the format defined in `docs/adr/template.md` and used for every ADR in this repo.

**File**: `docs/adr/ADR-NNN-kebab-case-title.md`

```markdown
---
doc_id: "7.N"
title: "ADR-NNN kebab case title"
section: "ADR"
summary: "One sentence: status + decision made."
updated: "YYYY-MM-DD"
---

# 7.N — ADR-NNN: Decision Title

**Status:** Accepted

**Date:** YYYY-MM-DD

## 7.N.1 Context

What situation or problem prompted this decision? Include:
- The system state that made a decision necessary
- Constraints or forces at play (technical, organizational, timeline)
- Why this had to be decided now rather than deferred

## 7.N.2 Decision

What was decided? Be specific and concrete. State the exact approach — not "we will consider X" but "we will use X for Y because Z."

## 7.N.3 Consequences

What changes as a result of this decision?

**Easier:** What becomes simpler, faster, or lower-risk.

**Harder:** What becomes more complex, constrained, or expensive.

**Risks accepted:** Residual risks that are not mitigated by the decision.

**Follow-up work:** Queue items or future decisions this decision defers or creates.

## 7.N.4 Alternatives Considered

Minimum two alternatives. Be honest about why each was rejected.

| Alternative | Rejected because |
|---|---|
| Option A | Specific reason with trade-off |
| Option B | Specific reason with trade-off |

## 7.N.5 References

- Links to relevant code files or modules
- Links to prior ADRs that informed this one
- Links to `docs/architecture/` documents affected by this decision
```

---

## Template 2 — MADR Variant (Multi-Option Comparison)

**Use when**: the decision has 3+ real options with close scores in the pattern selection matrix, or when the decision will be questioned by future contributors who need to see the full comparison.

**How to use**: start with the Extended Nygard template, then replace the Alternatives Considered section with the expanded MADR structure below.

```markdown
## Decision Drivers

- [Most important quality attribute scenario — e.g., "Availability: system must survive DB node failure"]
- [Second driver — e.g., "Team familiarity: no prior NoSQL experience"]
- [Third if needed]

## Considered Options

- Option A — [brief label]
- Option B — [brief label]
- Option C — [brief label]

## Decision Outcome

Chosen option: **Option A**, because [1–2 sentence rationale tied directly to the decision drivers].

### Consequences

- Good: [what this decision enables]
- Bad: [what this costs or introduces as a risk]

### Confirmation

[How will we confirm this decision was correct? E.g., "Performance benchmark after 3 months of production load."]

## Pros and Cons of the Options

### Option A

- Pro: [strength tied to a decision driver]
- Pro: [second strength]
- Con: [weakness]
- Con: [second weakness]

### Option B

- Pro: [strength]
- Con: [weakness tied to why it was rejected]

### Option C

- Pro: [strength]
- Con: [decisive weakness]
```

### MADR Example — Database Selection

```markdown
## Decision Drivers

- Availability: system must remain partially functional during DB node failure
- Team familiarity: team has 3 years of PostgreSQL operational experience
- Data model: primary data is relational with occasional JSON attributes

## Considered Options

- PostgreSQL
- MySQL
- MongoDB

## Decision Outcome

Chosen option: **PostgreSQL**, because it satisfies the availability driver via streaming replication,
matches the team's existing operational knowledge, and its JSONB support handles semi-structured
attributes without a separate store.

## Pros and Cons of the Options

### PostgreSQL

- Pro: ACID transactions, mature ecosystem, strong team familiarity
- Pro: JSONB handles semi-structured data without a separate store
- Con: Horizontal sharding requires significant effort (accepted: not needed at current scale)

### MySQL

- Pro: Widely supported; InnoDB provides ACID guarantees
- Con: JSON support weaker than PostgreSQL JSONB
- Con: Team has no MySQL operational experience — adds ramp-up risk

### MongoDB

- Pro: Document model fits the product's primary data shape
- Con: Team has no MongoDB experience; adds operational learning curve
- Con: Eventual consistency model complicates transaction design for billing
```

---

## Template 3 — Y-Statement (Summary Format)

**Use when**: generating the `summary` field in ADR frontmatter, or producing a decision log overview. The Y-statement is a compact single-sentence format — it supplements an ADR, it does not replace it.

**Format**:
```
In the context of [situation],
facing [concern or quality attribute],
we decided [the option chosen],
to achieve [desired quality],
accepting [downside or tradeoff].
```

**Example**:
```
In the context of the payment processing module needing to scale independently,
facing a requirement for zero-downtime deployments and independent release cycles,
we decided to extract payments into a separate service with its own database,
to achieve deployment independence and team autonomy,
accepting the overhead of distributed transaction management for cross-service operations.
```

Use the Y-statement as the `summary` value in ADR frontmatter for decisions where context compression matters:

```yaml
summary: "Accepted: extracted payments as a separate service to achieve deployment independence, accepting distributed transaction overhead."
```

---

## Template 4 — Tyree-Ackerman (Compliance / Enterprise)

**Use when**: the decision has compliance or audit requirements, involves multiple teams who need a formal record, or is enterprise-level infrastructure (cloud provider choice, data residency, multi-region strategy).

```markdown
# [Decision Title]

| Field | Value |
|---|---|
| Issue | [The architectural problem or question to resolve] |
| Decision | [The architectural decision made] |
| Status | Proposed / Accepted / Deprecated |
| Group | [Architectural area: data, integration, security, infrastructure, etc.] |
| Assumptions | [What assumptions underlie this decision?] |
| Constraints | [What constraints forced or shaped the decision?] |
| Positions | [What options were considered?] |
| Argument | [Why was the chosen option selected over the others?] |
| Implications | [What does this mean for the system? Other decisions now required?] |
| Related Decisions | [ADR numbers that this decision depends on or affects] |
| Related Requirements | [QAS IDs or requirement IDs satisfied by this decision] |
| Related Artifacts | [Design docs, diagrams, spikes referenced] |
| Notes | [Additional notes, dissenting opinions, future reconsideration triggers] |
```

---

## ADR File Organization in This Repo

```
docs/adr/
  README.md                              ← auto-generated by make adr-index
  template.md                            ← base template (do not hand-edit README.md)
  0001-initial-architecture.md           ← founding ADR, multi-decision format
  ADR-002-async-task-queue.md            ← subsequent ADRs in standard format
  ADR-003-jwt-auth-strategy.md
```

Naming rules:
- Zero-padded three-digit number for ADR-002 onward
- Kebab-case title that is meaningful without opening the file
- Lowercase only, no underscores
- `0001-initial-architecture.md` is a special case (founding ADR)

---

## Status Lifecycle

```
Proposed → Accepted → Deprecated
                    ↘ Superseded by ADR-NNN
```

| Status | Meaning |
|---|---|
| **Proposed** | Under consideration; not yet active |
| **Accepted** | The current active decision |
| **Deprecated** | Was accepted; now discouraged; not yet replaced |
| **Superseded by ADR-NNN** | Replaced by a new decision; link the replacement |

When superseding: update both ADRs. Old ADR gets `Superseded by ADR-NNN`. New ADR gets `**Supersedes:** ADR-NNN` below the Status line.

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Decision-only ADR | Records choice but not why; future agents can't evaluate it | Always document options considered and the rationale |
| Hindsight ADR | Written after implementation to justify a done deal | Write during the decision, before implementation — context is lost afterward |
| Compound ADR | Multiple decisions in one document | One ADR per decision; split if scope creeps |
| Vague context | "We needed something scalable" | Name the quality attribute scenario and its metric |
| No status updates | ADRs become stale and misleading | Supersede or deprecate; never silently delete |
| Obvious-decision skipped | "Everyone agreed so no ADR needed" | Obvious decisions are re-litigated most — always document alternatives |
