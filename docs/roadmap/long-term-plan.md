---
doc_id: "24.1"
title: "DeviceLab long-term implementation plan"
section: "Roadmap"
status: "current"
completion: "0%"
updated: "2026-05-31"
---

# DeviceLab — Long-term Implementation Plan

## Strategic outcome

A local-first, open-source BYOC control plane that lets a human or AI agent create and operate cloud-backed device environments in their own AWS account. The end product must feel like an operational tool — predictable setup, explicit costs, safe secrets, reproducible automation, and strong evidence for every meaningful action.

Three durable advantages drive every sequencing decision:

1. **Agent-native first.** MCP is not an afterthought. Observation, actions, recipes, and evidence must be structured for low round-trip agent loops.
2. **User-owned infrastructure.** All cloud runtime resources live in the user's AWS account. No DeviceLab-hosted SaaS, no billing plane.
3. **Auditable safety.** Cost, secret, lifecycle, and dangerous-mode controls are visible, testable, and replayable from day one.

---

## OSS dependency map

Every major subsystem is backed by a specific open-source repo. This table is the source of truth — do not introduce new dependencies without an ADR.

| Subsystem | Package / source | How we use it |
|-----------|-----------------|---------------|
| MCP server | `mcp` (`pip install mcp`) via FastMCP | The entire MCP gateway layer — server, tool registration, capability handshake, transport |
| WebRTC streaming | `aiortc` (`pip install aiortc`) | Media stream + split input data channel; `examples/datachannel-cli` is the seed pattern |
| Browser adapter | `browser-use` (`pip install browser-use`) | `browser_use/browser/`, `browser_use/dom/`, `browser_use/controller/` — ported to the Browser adapter SPI |
| Android control | `uiautomator2` (`pip install uiautomator2`) + `adb` subprocess | AX tree extraction and touch/key input for Android family adapter |
| Android AX reference | `appium/appium-uiautomator2-driver` | `lib/commands/` is the reference for every Android action; port patterns, not code |
| AX tree scripts | `viralmind-ai/accessibility-tree-parsers` | Copy three scripts directly: `windows_ax.py`, `macos_ax.py`, `linux_ax.py` into `apps/api/app/adapters/ax/` |
| AWS pricing | `awspricing` (`pip install awspricing`) | Pricing lookup + cache for cost estimates and guardrail calculations |
| AWS provisioning reference | `cloud-custodian` | `c7n/resources/ec2.py` and `c7n/tags.py` — reference for EC2 lifecycle + tagging; do not import the package, port the patterns |
| Recipe DSL | `pypyr` (`pip install pypyr`) | Recipe step executor; DeviceLab writes custom step modules on top |
| Secrets | `keyring` (`pip install keyring`) | OS keychain backend for SecretRef storage; wraps platform keychain on Mac/Linux/Windows |
| Network proxy | `mitmproxy` (`pip install mitmproxy`) | Embeddable proxy with custom addon for network capture and injection |
| Audit log | `lulzasaur9192/agent-audit-log-examples` | Copy ~100 lines of HMAC-SHA256 hash-chain logic into `apps/api/app/core/audit_log.py`; do not pip install |
| Runtime agent | Written from scratch | STF (`openstf/stf`) `provider/` + `agent/` split is the architecture reference; AgentScope execution loop is secondary reference |
| Device FSM | `pytransitions` (`pip install transitions`) | State machine for device lifecycle (requested → … → terminated) |

---

## Phase map

| Phase | Theme | Key deliverable |
|-------|-------|-----------------|
| 01 | Local foundation | Control plane runs safely on localhost; device FSM wired; operator has a clear path |
| 02 | BYOC provisioning MVP | AWS preflight + Linux device full lifecycle + browser session baseline |
| 03 | MCP observation + interaction | Agents discover capabilities, observe AX/OCR structure, execute batched semantic actions |
| 04 | Recipes, identity, streaming | Recipes execute repeatably; secrets never leave keychain; split WebRTC stream + input channel |
| 05 | Guardrails, artifacts, replay | Cost caps enforced; snapshots + test artifacts exist; evidence replay explains every action |
| 06 | Adapter SPI + family expansion | Versioned plugin contract; Android, Windows, macOS, iOS Sim, real iOS added through adapters |

---

## End-state component map

```
Local Machine (developer laptop)
├── Web UI (apps/web)           React 19 + Vite + TanStack
├── Control API (apps/api)      FastAPI + SQLModel + Postgres
│   ├── Device Lifecycle Service    pytransitions FSM
│   ├── Cloud Integration Layer     boto3 + awspricing
│   ├── Observation + Action Hub    AX/OCR/screenshot/VLM tiers
│   ├── Identity Broker             keyring + SecretRef
│   ├── Cost Guardrail Service      awspricing + soft/hard cap FSM
│   ├── Recipe Runner               pypyr + custom step modules
│   ├── Artifact + Evidence Store   HMAC audit log + S3
│   └── Adapter SPI                 versioned plugin contract
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
