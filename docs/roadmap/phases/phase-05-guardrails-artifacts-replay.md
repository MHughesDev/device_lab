---
doc_id: "24.6"
title: "Phase 05 - Guardrails, artifacts, and replay"
section: "Roadmap"
status: "current"
completion: "0%"
summary: "Detailed implementation plan for cost guardrails, snapshots, forks, test artifacts, evidence persistence, and replay timelines."
updated: "2026-05-30"
---

# Phase 05 - Guardrails, Artifacts, and Replay
<!-- derived from: queue/queue.csv Q-112 Q-113 Q-114 Q-115, docs/security/threat-model.md, docs/architecture/data-model.md -->

## Objective

Close the safety and accountability loop before broad device expansion. Every expensive lifecycle action should be policy-checked, every test run should produce retrievable artifacts, and every MCP action should be replayable with evidence.

## Scope

In scope:

- Cost policy model with soft and hard caps.
- Active resource inventory and orphan cleanup suggestions.
- Snapshot and fork lifecycle contracts.
- Test run service with JUnit output and artifact manifest.
- Evidence records linking MCP calls to before/after observations.
- Replay timeline API.
- Retention and purge behavior.

Out of scope:

- Perfect billing reconciliation for every AWS edge case.
- Enterprise policy engine.
- Long-term cold storage.
- Full snapshot support for unsupported family/provider combinations.

## Implementation Sequence

1. Add cost policy model.
   Define workspace caps, per-device estimates, action budgets, soft warning thresholds, hard blocks, and override policy.

2. Wire lifecycle guard checks.
   Before create, start, snapshot, fork, or long-running recipe execution, evaluate policy. Return explicit block/warning payloads.

3. Implement pricing and inventory adapters.
   Cache pricing lookups, list tagged resources, and compare active DeviceLab records with provider reality.

4. Add cleanup suggestions.
   Identify orphaned or stale resources and propose safe cleanup actions. Dangerous cleanup requires confirmation and audit.

5. Implement snapshot manager.
   Support `snapshot_start`, `snapshot_status`, and `fork_from_snapshot` where the family adapter declares support. Unsupported paths return capability errors.

6. Build test run service.
   Run smoke/suite definitions against a device/session, persist status, and emit JUnit plus optional Allure-compatible metadata.

7. Create artifact manifest.
   Store logs, screenshots, recordings, traces, recipe output, JUnit, and diagnostics behind a consistent metadata and retrieval API.

8. Persist evidence records.
   For every MCP action, store request metadata, policy decisions, before/after screen versions, observation delta, warnings, and artifact links.

9. Add replay timeline.
   Provide ordered session and recipe timelines for debugging, review, and reproducibility.

## Data Contracts

| Entity | Purpose |
|---|---|
| `CostEstimate` | Estimated current and projected cost by device/action/workspace. |
| `Snapshot` | Snapshot request, provider id, family support, state, source device, created time. |
| `TestRun` | Test execution status, target device/session, suite metadata, summary. |
| `Artifact` | File metadata, type, storage path, retention, associated run/session/evidence. |
| `Evidence` | MCP/API action envelope with before/after observation links and policy decisions. |

## Policy Behavior

- Soft cap: action proceeds only with visible warning and audit event.
- Hard cap: action is blocked unless a privileged explicit override exists.
- Unknown estimate: default to conservative warning or block depending on action cost class.
- Cleanup: never delete untagged resources automatically.

## Testing and Verification

- Unit test cost policy decisions for soft, hard, unknown, and override cases.
- Integration-test snapshot unsupported-family error handling.
- Validate JUnit XML output shape.
- Test artifact manifest retrieval and retention purge.
- Test replay timeline ordering and evidence linkage.

## Exit Criteria

- Expensive lifecycle actions pass through cost policy.
- Snapshot/fork contract exists and works for at least one supported path or returns clear capability errors.
- Test runs produce retrievable JUnit/artifact bundles.
- MCP evidence can reconstruct before/after action history for a session.

