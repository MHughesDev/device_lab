---
doc_id: "24.0"
title: "Roadmap overview"
section: "Roadmap"
status: "current"
completion: "58%"
summary: "Index for DeviceLab long-term and phase-by-phase implementation plans."
updated: "2026-06-01"
---

# Roadmap Overview

**Progress: 58%** `██████░░░░` — 7 of 12 phases complete (01–07); Phase 08 next.

This folder turns the initialized DeviceLab product contract into an implementation roadmap. The queue remains the execution source of truth for individual tasks, while these plans explain the intended sequence, architecture depth, handoff expectations, and exit gates across larger phases.

## Plans

| ID | Plan | Status | Purpose |
|---|---|---|---|
| 24.1 | [Long-term plan](long-term-plan.md) | 58% | End-to-end delivery strategy from local-first foundation to ecosystem-ready platform. |
| 25.0 | [Interactive Device Workspace plan](interactive-workspace-plan.md) | 0% | Human-facing low-latency interactive layer (phases 08–12) on top of the local-first runtime. |
| 24.2 | [Phase 01 - Local foundation](phases/phase-01-local-foundation.md) | ✅ 100% | Make the repo runnable, local-only by default, and ready for product feature work. |
| 24.3 | [Phase 02 - BYOC provisioning MVP](phases/phase-02-byoc-provisioning-mvp.md) | ✅ 100% | Connect AWS, run preflight, and ship first Linux/browser device lifecycle paths. |
| 24.4 | [Phase 03 - MCP observation and interaction](phases/phase-03-mcp-observation-interaction.md) | ✅ 100% | Deliver capability-aware MCP tools, structured observation, and batched semantic actions. |
| 24.5 | [Phase 04 - Recipes, identity, and streaming](phases/phase-04-recipes-identity-streaming.md) | ✅ 100% | Add repeatable recipes, safe secret references, and split media/input sessions. |
| 24.6 | [Phase 05 - Guardrails, artifacts, and replay](phases/phase-05-guardrails-artifacts-replay.md) | ✅ 100% | Enforce cost policy, snapshots, test artifacts, and evidence replay. |
| 24.7 | [Phase 06 - Adapter SPI and family expansion](phases/phase-06-plugins-family-expansion.md) | ✅ 100% | Stabilize the adapter SPI and expand across all target device families. |
| 24.8 | [Phase 07 - Local hosting](phases/phase-07-local-hosting.md) | ✅ 100% | Host device families directly on the local machine via a transport abstraction, local scheduler, and placement layer (ADR-0003). |
| 25.1 | [Phase 08 - Display & resource foundations](phases/phase-08-display-resource-foundations.md) | ⬜ 0% | Real framebuffers per family; 4-axis device model; Host Resource Ledger; per-device log bus. |
| 25.2 | [Phase 09 - Low-latency streaming media layer](phases/phase-09-streaming-media-layer.md) | ⬜ 0% | `MediaSource`/`InputSink` SPI; HW capture+encode; video+audio+input; attach/detach. |
| 25.3 | [Phase 10 - Device manifests & environment registry](phases/phase-10-device-manifests.md) | ⬜ 0% | Declarative `DeviceManifest` (recipe, not disk image); registry; capture/create-from-manifest. |
| 25.4 | [Phase 11 - Device workspace UI](phases/phase-11-device-workspace-ui.md) | ⬜ 0% | Browser-tab UX; New/Existing wizard; screen pane + log panel; full options menu; naming. |
| 25.5 | [Phase 12 - Root & cloud infra settings](phases/phase-12-root-settings-cloud-infra.md) | ⬜ 0% | Server-level settings: cloud infra, local host budget, streaming, MCP, manifests, security. |

## How to use these files

- Use the long-term plan to understand product sequencing and major architectural bets.
- Use a phase file before creating or decomposing queue rows for that phase.
- Treat exit gates as release blockers for the phase, not suggestions.
- Keep the queue granular. A phase item should usually split into multiple S/M rows before implementation.
- Update the relevant phase file when implementation reality changes a milestone, dependency, interface, or risk.

