---
doc_id: "24.0"
title: "Roadmap overview"
section: "Roadmap"
status: "current"
summary: "Index for DeviceLab long-term and phase-by-phase implementation plans."
updated: "2026-05-30"
---

# Roadmap Overview

This folder turns the initialized DeviceLab product contract into an implementation roadmap. The queue remains the execution source of truth for individual tasks, while these plans explain the intended sequence, architecture depth, handoff expectations, and exit gates across larger phases.

## Plans

| ID | Plan | Purpose |
|---|---|---|
| 24.1 | [Long-term plan](long-term-plan.md) | End-to-end delivery strategy from local-first foundation to ecosystem-ready platform. |
| 24.2 | [Phase 01 - Local foundation](phases/phase-01-local-foundation.md) | Make the repo runnable, local-only by default, and ready for product feature work. |
| 24.3 | [Phase 02 - BYOC provisioning MVP](phases/phase-02-byoc-provisioning-mvp.md) | Connect AWS, run preflight, and ship first Linux/browser device lifecycle paths. |
| 24.4 | [Phase 03 - MCP observation and interaction](phases/phase-03-mcp-observation-interaction.md) | Deliver capability-aware MCP tools, structured observation, and batched semantic actions. |
| 24.5 | [Phase 04 - Recipes, identity, and streaming](phases/phase-04-recipes-identity-streaming.md) | Add repeatable recipes, safe secret references, and split media/input sessions. |
| 24.6 | [Phase 05 - Guardrails, artifacts, and replay](phases/phase-05-guardrails-artifacts-replay.md) | Enforce cost policy, snapshots, test artifacts, and evidence replay. |
| 24.7 | [Phase 06 - Plugins and family expansion](phases/phase-06-plugins-family-expansion.md) | Stabilize the adapter SPI and expand across all target device families. |

## How to use these files

- Use the long-term plan to understand product sequencing and major architectural bets.
- Use a phase file before creating or decomposing queue rows for that phase.
- Treat exit gates as release blockers for the phase, not suggestions.
- Keep the queue granular. A phase item should usually split into multiple S/M rows before implementation.
- Update the relevant phase file when implementation reality changes a milestone, dependency, interface, or risk.

