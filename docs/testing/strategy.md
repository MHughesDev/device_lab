---
doc_id: "22.1"
title: "testing strategy"
section: "Testing"
status: "current"
summary: "DeviceLab validation strategy spanning unit/integration/e2e, MCP contract tests, and round-trip budget gates."
updated: "2026-05-17"
---

# Testing Strategy
<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §15 §17 -->

## Test pyramid

- **Unit tests:** state machine transitions, adapter capability mapping, identity broker, pricing calculator, envelope validation.
- **Integration tests:** REST routers + service layers with mocked AWS interfaces, runtime-agent simulation, persistence checks.
- **End-to-end tests (human):** Playwright UI flows (onboarding, device create/stream open, recipe run, artifact download).
- **End-to-end tests (AI):** MCP contract suites validating capability handshake, observation/action envelopes, and permission gates.
- **Cloud smoke tests:** nightly opt-in real AWS jobs for each supported family.

## Domain-critical test suites

1. **Lifecycle correctness:** invalid transition rejection, phase progression, recovery behavior.
2. **Safety controls:** dangerous action confirmations, cap enforcement, secret non-disclosure.
3. **Observation/action contract:** screen-version guards and no-back-and-forth action semantics.
4. **Cost accuracy:** pricing cache behavior and cap threshold event emission.

## Quality gates

- Preserve or raise global coverage floor from `pyproject.toml`.
- Fail CI when round-trip-budget tests exceed published call budgets for baseline flows.
- Validate artifact/evidence bundle integrity and replay compatibility.

## Regression strategy

- Every bugfix adds a failing test first (or same PR) in relevant layer.
- Per-family smoke recipes execute against known-good templates.
- Contract changes in MCP envelopes require golden test updates and compatibility notes.
