---
doc_id: "24.1"
title: "DeviceLab long-term implementation plan"
section: "Roadmap"
status: "current"
completion: "0%"
summary: "Long-term phased implementation strategy for DeviceLab, spanning foundation, BYOC provisioning, MCP automation, safety, replay, plugins, and device family expansion."
updated: "2026-05-30"
---

# DeviceLab Long-term Implementation Plan
<!-- derived from: spec/spec.md section 18, queue/queue.csv mvp batches, docs/architecture/overview.md, docs/architecture/bounded-contexts.md -->

## Strategic outcome

DeviceLab should become a local-first, open-source control plane that lets a human or AI agent create and operate cloud-backed device environments in the user's own AWS account. The long-term product must feel like an operational tool, not a demo: predictable setup, explicit costs, safe secrets, reproducible automation, and strong evidence for every meaningful action.

The platform should optimize for three durable advantages:

1. **Agent-native operation:** MCP is not an afterthought. Device capabilities, observations, actions, recipes, and evidence must be structured for low round-trip agent work.
2. **User-owned infrastructure:** all cloud runtime resources live in the user's account, with local control plane defaults and no DeviceLab-hosted SaaS dependency.
3. **Auditable safety:** cost, secret, lifecycle, and dangerous-mode controls must be visible, testable, and replayable.

## Delivery principles

- Build the smallest vertical slice that proves each layer before broadening device family coverage.
- Prefer typed service contracts over route-level logic so REST, UI, and MCP can share behavior.
- Keep runtime actions idempotent and resumable because cloud operations, streams, and agents fail mid-flight.
- Make every expensive or destructive action pass through guardrail, confirmation, and audit paths.
- Treat documentation, queue rows, tests, and runbooks as implementation artifacts.

## Phase map

| Phase | Theme | Primary queue alignment | Main proof |
|---|---|---|---|
| 01 | Local foundation | Q-101 and prerequisite template cleanup | Local control plane runs safely on localhost and operators know the command path. |
| 02 | BYOC provisioning MVP | Q-102 through Q-105 | AWS preflight plus Linux/browser lifecycle vertical slice. |
| 03 | MCP observation and interaction | Q-106 through Q-108 | Agents can discover capabilities, observe structure, and execute batched semantic actions. |
| 04 | Recipes, identity, and streaming | Q-109 through Q-111 | Humans and agents can stream, record/replay recipes, and inject secrets without exposing values. |
| 05 | Guardrails, artifacts, and replay | Q-112 through Q-115 | Costs are enforced, snapshots/test artifacts exist, and evidence replay explains actions. |
| 06 | Plugins and family expansion | Q-116 plus new family rows | Adapter SPI supports first external-style adapter and remaining families are sequenced. |

## Target architecture by the end state

The end-state architecture should keep these components explicit:

- **Local Web UI:** onboarding, workspace status, session stream, cost view, artifacts, replay.
- **Local API:** workspace, cloud account, device lifecycle, recipes, artifacts, cost, audit, MCP config.
- **MCP Gateway:** capability handshake, tool manifest generation, observation/action tools, subscriptions.
- **Device Lifecycle Service:** templates, profiles, lifecycle state machine, warm pools, snapshot/fork flows.
- **Cloud Integration Layer:** AWS auth modes, preflight checks, CloudFormation/SSM/EC2/Device Farm orchestration.
- **Runtime Agent:** cloud-side process for observation, action execution, streaming, file/artifact capture.
- **Observation and Action Hub:** screen versioning, AX/OCR/screenshot/VLM tiers, semantic actions, batched steps.
- **Identity Broker:** keychain-backed secret references, MCP elicitation, injection audit.
- **Cost Guardrail Service:** pricing cache, caps, orphan cleanup, budget-aware lifecycle gating.
- **Artifacts and Evidence Store:** test outputs, logs, screenshots, MCP before/after envelopes, replay timeline.
- **Adapter SPI:** versioned adapter contract for device families and third-party cloud/runtime integrations.

## Implementation sequence

1. **Stabilize the local skeleton.**
   Confirm the app starts locally, binds only to localhost by default, and has a clear operator path. Fill documentation gaps that would cause feature agents to guess.

2. **Build the AWS account path before device breadth.**
   Implement credential selection, region checks, quota/IAM preflight, bootstrap status, and actionable failure messages. Do not create device lifecycle complexity until account readiness is inspectable.

3. **Ship one cloud device vertical slice.**
   Linux is the first full lifecycle target because it is the simplest place to validate provisioning, SSM, runtime agent bootstrapping, lifecycle events, streaming handoff, cleanup, and cost tags.

4. **Add browser parity as a second slice.**
   Browser sessions prove that DeviceLab is not only VM management. Use Playwright-backed runtime behavior to validate capability maps and higher-level interaction affordances.

5. **Make MCP the primary automation contract.**
   Add capability handshake, filtered manifests, observation envelopes, semantic actions, and `run_steps` batching. Every UI action that matters should eventually map to the same underlying services.

6. **Layer recipes, identity, and streaming.**
   Add repeatable workflows, secret references, and split media/input transport after the action model is stable enough to record and replay.

7. **Close safety and evidence loops.**
   Cost caps, snapshots, artifact bundles, and replay should land before family expansion accelerates. Otherwise every later family multiplies blind spots.

8. **Stabilize adapter SPI and expand families.**
   Once lifecycle, observation, action, stream, cost, and evidence contracts are mature, expand to Android, Windows, macOS, iOS Simulator, and real iOS through adapters with explicit capability declarations.

## Cross-cutting workstreams

| Workstream | Long-term requirement |
|---|---|
| Data model | Stable entities for workspaces, cloud accounts, templates, devices, sessions, snapshots, recipes, runs, artifacts, evidence, secret refs, costs, audit events, and warm pools. |
| Auth and permissions | Local operator auth plus scoped MCP client roles; dangerous mode requires confirmation and audit. |
| Runtime protocol | mTLS channel, resumable commands, typed observation/action envelopes, stream negotiation, artifact upload. |
| Observability | Structured logs, lifecycle events, metrics for latency/cost/action success, and trace correlation across MCP/API/runtime. |
| Testing | Unit tests for services, integration tests with fake AWS/runtime adapters, contract tests for MCP tools, E2E smoke for onboarding and first session. |
| Documentation | API docs, runbooks, threat model, queue rows, and roadmap files updated as features land. |

## Milestone exit gates

A phase is not done until:

- Its user-facing happy path is documented and runnable.
- Its service contracts have tests, including failure cases.
- Its dangerous or expensive paths pass through policy checks.
- Queue rows for delivered work are archived or clearly marked complete by the repo process.
- Any discovered follow-up is captured as a queue row or open question.

## Long-term risks

| Risk | Mitigation |
|---|---|
| AWS provisioning complexity swallows early product value | Keep phase 02 vertical and fake/substitute runtime boundaries where useful, but do not fake preflight or cleanup semantics. |
| MCP tool surface becomes too broad for agents to use well | Capability-filter tools by family and permission; keep envelopes consistent; add examples and contract tests. |
| Streaming dominates the roadmap before semantic automation works | Ship structured observation/action first; streaming is for human parity and high-fidelity inspection, not the primary AI loop. |
| Cost safety arrives too late | Add cost tags and guardrail extension points during lifecycle work, then enforce caps in phase 05. |
| Family expansion causes duplicate logic | Make adapters declare capabilities and delegate shared lifecycle/observation/action behavior to common services. |

