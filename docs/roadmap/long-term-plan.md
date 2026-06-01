---
doc_id: "24.1"
title: "DeviceLab long-term implementation plan"
section: "Roadmap"
status: "current"
completion: "67%"
updated: "2026-05-31"
---

# DeviceLab — Long-term Implementation Plan

**Progress:** six phases complete; Phase 07 (local hosting) planned

## Strategic outcome

A local-first, open-source BYOC control plane that lets a human or AI agent create and operate cloud-backed device environments in their own AWS account. The end product must feel like an operational tool — predictable setup, explicit costs, safe secrets, reproducible automation, and strong evidence for every meaningful action.

Three durable advantages drive every sequencing decision:

1. **Agent-native first.** MCP is not an afterthought. Observation, actions, recipes, and evidence must be structured for low round-trip agent loops.
2. **User-owned infrastructure.** All cloud runtime resources live in the user's AWS account. No DeviceLab-hosted SaaS, no billing plane.
3. **Auditable safety.** Cost, secret, lifecycle, and dangerous-mode controls are visible, testable, and replayable from day one.

---

## How to use these plans with Claude

These plan files are the source of truth for AI-assisted implementation. Follow this two-step pattern:

### Step 1 — Plan with Sonnet (Max mode)
Open the relevant phase plan. Ask Claude to:
- Clarify ambiguous tasks
- Identify missing edge cases or integration points
- Update the plan before implementation begins
- Sequence tasks into parallel batches

### Step 2 — Implement with Sonnet (Low/fast mode)
Point Claude at a specific task by ID (e.g., "implement task 05-04"). The task spec provides:
- **Files:** exact paths (new or existing)
- **Symbols:** exact class/function signatures with types
- **Wiring:** where to import and register
- **Tests:** exact test names and what each asserts
- **Do not:** explicit exclusions to prevent scope creep

Each task is sized to fit in one focused agent pass and produce one clean commit.

### Commit conventions
- One task = one commit
- Commit message format: `feat(phase-NN): <task-title>`
- Push to `claude/friendly-cannon-7fCKA` after each commit

---

## OSS dependency map

Every major subsystem is backed by a specific open-source repo. This table is the source of truth — do not introduce new dependencies without an ADR.

| Subsystem | Package / source | How we use it |
|-----------|-----------------|---------------|
| MCP server | `mcp` via FastMCP | MCP gateway layer — server, tool registration, capability handshake, transport |
| WebRTC streaming | `aiortc` | Media stream + split input data channel |
| Browser adapter | `browser-use` | `browser_use/browser/`, `browser_use/dom/`, `browser_use/controller/` |
| Android control | `uiautomator2` + `adb` subprocess | AX tree extraction and touch/key input |
| Android AX reference | `appium/appium-uiautomator2-driver` | `lib/commands/` — reference for Android actions; port patterns, not code |
| AX tree scripts | `viralmind-ai/accessibility-tree-parsers` | Copy `windows_ax.py`, `macos_ax.py`, `linux_ax.py` → `adapters/ax/` |
| AWS pricing | `awspricing` | Pricing lookup + cache for cost estimates and guardrail calculations |
| AWS provisioning reference | `cloud-custodian` | `c7n/resources/ec2.py` and `c7n/tags.py` — reference for EC2 lifecycle + tagging |
| Recipe DSL | `pypyr` | Recipe step executor; DeviceLab writes custom step modules on top |
| Secrets | `keyring` | OS keychain backend for SecretRef storage |
| Network proxy | `mitmproxy` | Embeddable proxy with custom addon for network capture and injection |
| Audit log | Written from scratch | HMAC-SHA256 hash-chain in `apps/api/app/core/audit_log.py` |
| Runtime agent | Written from scratch | STF `provider/` + `agent/` split is the architecture reference |
| Device FSM | `pytransitions` | State machine for device lifecycle |

---

## Phase map

| Phase | Status | Theme | Key deliverable |
|-------|--------|-------|-----------------|
| 01 | ✅ complete | Local foundation | Control plane runs safely on localhost; device FSM wired; operator has a clear path |
| 02 | ✅ complete | BYOC provisioning MVP | AWS preflight + Linux device full lifecycle + browser session baseline |
| 03 | ✅ complete | MCP observation + interaction | Agents discover capabilities, observe AX/OCR structure, execute batched semantic actions |
| 04 | ✅ complete | Recipes, identity, streaming | Recipes execute repeatably; secrets never leave keychain; split WebRTC stream + input channel |
| 05 | ✅ complete | Guardrails, artifacts, replay | Cost caps enforced; snapshots + test artifacts exist; evidence replay explains every action |
| 06 | ✅ complete | Adapter SPI + family expansion | Versioned plugin contract; Android, Windows, macOS, iOS Sim added through adapters |
| 07 | ⬜ planned | Local hosting | Channel transport abstraction + local scheduler + placement layer; host families on the local machine with no AWS account (ADR-0003) |

---

## End-state component map

```
Local Machine (developer laptop)
├── Web UI (apps/web)           React 19 + Vite + TanStack
├── Control API (apps/api)      FastAPI + SQLModel + Postgres
│   ├── Device Lifecycle Service    pytransitions FSM + cost guardrail hooks
│   ├── Cloud Integration Layer     boto3 + awspricing
│   ├── Observation + Action Hub    AX/OCR/screenshot/VLM tiers
│   ├── Identity Broker             keyring + SecretRef
│   ├── Cost Guardrail Service      CostPolicy + awspricing + soft/hard cap FSM
│   ├── Recipe Runner               pypyr + custom step modules
│   ├── Artifact + Evidence Store   HMAC audit log + S3 presigned URLs
│   ├── TestRun + Replay            JUnit XML, timeline, evidence cross-reference
│   └── Adapter SPI                 versioned plugin contract + registry
├── MCP Gateway                 FastMCP (mcp SDK)
└── Stream Gateway              aiortc (WebRTC + data channel)

User's AWS Account
├── EC2 instances (Linux, Windows, macOS Dedicated Host)
├── Android Emulator (nested virt on C8i/M8i)
├── AWS Device Farm (real iOS, Android)
└── Runtime Agent (cloud-side process, SSM-bootstrapped)
    ├── Observation layer       viralmind AX scripts + uiautomator2
    ├── Action layer            keyboard/mouse/touch via OS APIs
    ├── Stream source           aiortc peer
    └── Artifact capture        logs, screenshots, traces → S3
```

---

## Implementation sequence rationale

1. **Skeleton before devices.** The control plane needs to exist, be localhost-safe, and have a working database before anything provisions cloud resources.
2. **AWS account path before device breadth.** Credential selection, quota, IAM, and preflight must be inspectable before any device lifecycle code runs.
3. **Linux vertical slice first.** Linux is the simplest cloud device to validate provisioning → SSM bootstrap → runtime agent → lifecycle events → streaming → cleanup → cost tags.
4. **Browser second.** Proves DeviceLab is not just VM management; validates capability maps and semantic action contracts.
5. **MCP before recipes.** The action model must be stable before recording or replaying it.
6. **Recipes + secrets + streaming together.** They are interdependent — recipes inject secrets, streaming requires session tokens, reconnect requires both.
7. **Safety before breadth.** Cost caps, evidence, and replay land before family expansion. Every new family multiplies risk surface.
8. **Adapter SPI then families.** Once contracts are mature, families expand through clean adapter boundaries.

---

## Cross-cutting workstreams

| Workstream | Requirement |
|------------|-------------|
| Data model | Stable entities: workspace, cloud account, template, device, session, snapshot, recipe, run, artifact, evidence, secret ref, cost estimate, audit event |
| Auth | Local operator auth + scoped MCP client roles; dangerous mode requires confirmation + audit |
| Runtime protocol | mTLS channel, resumable commands, typed observation/action envelopes, stream negotiation, artifact upload |
| Observability | Structured logs, lifecycle events, metrics (latency/cost/action success), trace correlation across MCP/API/runtime |
| Testing | Unit tests for services, integration tests with fake AWS + runtime adapters, contract tests for MCP tools, E2E smoke for onboarding + first session |

---

## Phase exit gates (apply to every phase)

A phase is complete when:
- Its happy path is documented and runnable end-to-end.
- Every service contract has tests covering success and failure cases.
- Every dangerous or expensive path passes through a policy check.
- Any discovered follow-up is captured as a GitHub issue or open question.

---

## Long-term risks

| Risk | Mitigation |
|------|------------|
| AWS provisioning complexity swallows early value | Keep phase 02 vertical; use fake adapters in tests; do not fake preflight or cleanup semantics |
| MCP tool surface too broad for agents | Capability-filter by family + permission; keep envelopes consistent; add contract tests |
| Streaming dominates roadmap before semantic automation works | Ship AX observation/action first; streaming is human parity, not the AI loop |
| Cost safety arrives too late | Add cost tags during lifecycle work; enforce caps in phase 05 |
| Family expansion causes duplicate logic | Adapters declare capabilities and delegate to common services; SPI enforced by conformance tests |
