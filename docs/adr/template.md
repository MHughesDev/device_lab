---
doc_id: "7.1"
title: "template"
section: "ADR"
summary: "ADR template for new decisions."
updated: "2026-05-16"
---

# 7.1 — template

**Purpose:** Blank copyable template for new ADRs. Copy this file, rename to `ADR-NNN-kebab-case-title.md`, and fill every section. Do not leave placeholder text. See `skills/repo-governance/add-adr.md` for the full creation procedure.

---

## ADR-NNN: Decision Title

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-NNN

**Date:** YYYY-MM-DD

## Context

What situation or problem prompted this decision? Include:
- The system state that made a decision necessary
- Constraints or forces at play (technical, organizational, timeline)
- Why this had to be decided now rather than deferred

## Decision

What was decided? Be specific and concrete. State the exact approach — not "we will consider X" but "we will use X for Y because Z."

## Consequences

**Easier:** What becomes simpler, faster, or lower-risk.

**Harder:** What becomes more complex, constrained, or expensive.

**Risks accepted:** Residual risks that are not mitigated by the decision.

**Follow-up work:** Queue items or future decisions this decision defers or creates.

## Alternatives Considered

Minimum two alternatives. Be honest about why each was rejected.

| Alternative | Rejected because |
|---|---|
| Option A | Specific reason with trade-off |
| Option B | Specific reason with trade-off |

## References

- Links to relevant code files or modules
- Links to prior ADRs that informed this one
- Links to `docs/architecture/` documents affected by this decision
- External documentation, benchmarks, or articles that supported the decision
- `queue/queue.csv` row IDs if implementation work is tracked there
