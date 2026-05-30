---
doc_id: "7.4"
title: "ADR-0002 devicelab product default overrides"
section: "ADR"
status: "accepted"
updated: "2026-05-17"
---

# 7.4 - ADR-0002: DeviceLab product default overrides

**Status:** Accepted

**Date:** 2026-05-17

## Context

The template baseline ships with assumptions suitable for generic web products (remote account auth, CRUD-centric API examples, optional profile-driven expansion). DeviceLab intentionally diverges in several foundational directions:

- local-first operation with no SaaS account system,
- BYOC AWS control plane as a hard product boundary,
- MCP-first automation surface with structured observation contracts,
- cloud-device lifecycle orchestration and cost guardrails as core product capabilities.

These choices must be captured as explicit product ADR decisions so future queue execution does not drift back to template defaults.

## Decision

DeviceLab initialization adopts the following product-level defaults:

1. **Auth posture:** no hosted user-signup/auth tier; local operator + scoped MCP clients only.
2. **Cloud posture:** BYOC AWS only; no reseller billing or DeviceLab-operated tenancy.
3. **AI interface posture:** MCP capability handshake + structured observation/action envelopes are first-class; screenshot/VLM-only loops are fallback tiers.
4. **Safety posture:** dangerous operations require confirmation and audit logging; cost caps are enforced by design.
5. **Delivery posture:** no feature implementation during initialization; queue seeding defines the execution path.

## Consequences

**Easier:** product intent stays explicit, queue planning aligns with AI-first constraints, and unsafe defaults are rejected early.

**Harder:** more upfront docs/queue specificity is required before code execution; initialization outputs are larger than minimal template starts.

**Risks accepted:** some implementation choices remain open (for example runtime language and optional integrations) and are deferred to human-ops decisions.

**Follow-up work:** resolve `idea.md` section 19 open questions, then execute queued rows in dependency order.

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Keep template defaults and encode DeviceLab differences ad hoc in queue rows | This would scatter foundational decisions across many rows and increase drift risk. |
| Treat DeviceLab as a profile toggle under the template without ADR documentation | The divergence is architectural, not cosmetic; profile notes are insufficient for governance and review. |

## References

- `idea.md`
- `spec/spec.md`
- `docs/open-questions.md`
- `docs/architecture/overview.md`
- `docs/architecture/auth.md`
- `skills/init/repo_initialize.md`
