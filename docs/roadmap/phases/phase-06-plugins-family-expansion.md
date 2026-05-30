---
doc_id: "24.7"
title: "Phase 06 - Plugins and family expansion"
section: "Roadmap"
status: "current"
completion: "0%"
summary: "Detailed implementation plan for the adapter plugin SPI, compatibility checks, and expansion across Android, Windows, macOS, iOS Simulator, real iOS, and mature browser/Linux support."
updated: "2026-05-30"
---

# Phase 06 - Plugins and Family Expansion
<!-- derived from: queue/queue.csv Q-116, spec/spec.md section 18, docs/architecture/bounded-contexts.md -->

## Objective

Turn DeviceLab from two working vertical slices into a durable platform. Stabilize the adapter SPI, prove compatibility checks, and expand target device families without copying lifecycle, observation, action, cost, and evidence logic into each adapter.

## Scope

In scope:

- Versioned adapter SPI.
- Adapter registry and compatibility validation.
- Capability declarations feeding templates and MCP manifests.
- Family-specific adapters for Android, Windows, macOS, iOS Simulator, and real iOS.
- Family conformance test suite.
- Documentation for third-party adapter authors.

Out of scope:

- Public plugin marketplace.
- Hosted plugin signing service.
- Commercial device provider partnerships.
- Supporting every OS version permutation in v1.

## Implementation Sequence

1. Define adapter SPI package.
   Create interfaces for template discovery, preflight requirements, provision, bootstrap, observe, act, stream, snapshot, artifact capture, and cleanup.

2. Add version negotiation.
   Each adapter declares SPI version, product version constraints, supported families, feature flags, and required provider capabilities.

3. Build registry and loader.
   Load built-in adapters first. Add extension points for local adapter packages after safety checks. Reject incompatible or duplicate adapters with explicit errors.

4. Add conformance tests.
   Every adapter must pass lifecycle, capability, observation, action, cleanup, cost tagging, and evidence contract tests. Use fakes where provider access is expensive.

5. Refactor Linux/browser into adapters.
   Move any hardcoded family logic behind the SPI so later families follow the same route.

6. Sequence Android.
   Support emulator or cloud Android path first, with Appium/ADB capabilities, structured observation, input, artifacts, and cleanup.

7. Sequence Windows.
   Add Windows lifecycle, runtime agent install, UIA observation, PowerShell/script gates, stream, and artifacts.

8. Sequence macOS and iOS Simulator.
   Handle host constraints, Apple licensing assumptions, simulator lifecycle, accessibility permissions, and stream/input behavior.

9. Sequence real iOS.
   Integrate AWS Device Farm or supported BYOC-compatible pathway. Keep capabilities explicit where real-device constraints differ from simulator behavior.

10. Publish adapter author docs.
   Document required methods, security expectations, capability declarations, test fixtures, and failure modes.

## Adapter Capability Declaration

| Capability | Required detail |
|---|---|
| Lifecycle | Supported actions, async behavior, cleanup requirements. |
| Observation | AX/UIA/OCR/screenshot/VLM support, tier ordering, version semantics. |
| Interaction | Semantic targets, coordinate fallback policy, keyboard/pointer/touch support. |
| Streaming | Media protocol, input channel support, reconnect behavior. |
| Artifacts | Logs, screenshots, recordings, traces, test outputs. |
| Cost | Estimate fields, tags, provider inventory support. |
| Snapshot | Supported states, forkability, provider limitations. |
| Security | Required permissions, dangerous actions, secret injection support. |

## Family Sequencing

| Family | Why this order | First proof |
|---|---|---|
| Linux | Baseline adapter and runtime agent proving cloud VM lifecycle. | Provision, stream, observe, terminate. |
| Browser | High-value automation target with Playwright semantics. | Create session, semantic browser actions, artifacts. |
| Android | Validates mobile automation path with Appium/ADB style controls. | Launch app/browser, observe, interact, collect logs. |
| Windows | Validates UIA, Windows bootstrap, and heavier VM lifecycle. | Provision, UIA observe, stream, artifact capture. |
| macOS | Validates Apple host constraints and accessibility permissions. | Provision supported path, observe, stream. |
| iOS Simulator | Shares macOS constraints but adds simulator lifecycle. | Boot simulator, run app/browser, collect artifacts. |
| Real iOS | Highest constraint and provider complexity. | Capability-limited real device session with clear unsupported paths. |

## Testing and Verification

- SPI compatibility tests reject unsupported versions.
- Built-in adapters pass shared conformance suite.
- MCP manifest changes when adapter capabilities change.
- Family docs list supported and unsupported actions.
- Cleanup tests verify no provider resource leaks for each family path.

## Exit Criteria

- Linux and browser run through the same adapter SPI as later families.
- At least one additional family passes conformance tests end to end.
- Unsupported capabilities return structured errors rather than hidden no-ops.
- External adapter authors can build against documented contracts.

