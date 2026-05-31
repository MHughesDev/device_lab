---
doc_id: "23.14"
title: "End-state capabilities (research copy)"
section: "Research"
summary: "Copy of docs/product/end-state-capabilities.md (doc 25.1) kept alongside research notes for cross-reference. Canonical version is 25.1."
updated: "2026-05-30"
---

# 25.1 — End-State Capabilities

This file is the canonical, exhaustive list of every feature and capability DeviceLab must have when it is complete. Nothing here is aspirational or speculative — every item is derived from `spec/spec.md`, the phase roadmap docs, the architecture docs, the API docs, and the queue. If a capability is not listed here it is not part of the end-state contract.

---

## 1. Device Families

Every family below must be a first-class citizen: provisionable, observable, interactable, streamable, snapshotable (where the family permits), testable, and cleanable.

- **Linux VM** — a full Linux machine (Ubuntu 24.04 baseline) running on EC2, reachable via SSM, with a runtime agent bootstrapped on it
- **Browser** — a real Chromium/Firefox browser session running in the cloud, automated via Playwright and exposed through the same observation/action contract as all other families
- **Android emulator** — an Android device simulation running in a cloud VM, controlled via ADB and Appium
- **Windows VM** — a full Windows machine running on EC2
- **macOS host/VM** — a Mac running in AWS (mac1/mac2 bare-metal instances), with special cost warning gates because of minimum billing commitment
- **iOS Simulator** — Apple's software iPhone/iPad simulator running on a cloud Mac, controlled via Xcode tooling
- **Real iOS device** — a physical iPhone or iPad connected through AWS Device Farm
- **Plugin-defined families** — any additional device type added via the adapter SPI without modifying DeviceLab core

---

## 2. Device Lifecycle

### 2.1 Templates and Profiles
- A template catalog listing every available device type, its image/source, supported regions, minimum resource requirements, capability declarations, streaming adapter, and automation adapter
- Device profiles that define instance sizing, auto-stop timeout, and snapshot policy, independent of the template

### 2.2 State Machine
Every device passes through a defined, observable state machine with no hidden transitions:
- `requested` → `preflight_blocked` → `provisioning` → `bootstrapping_agent` → `ready` → `stopping` → `stopped` → `terminating` → `terminated` → `failed`
- Sub-step detail within each state (e.g. "installing runtime agent, step 3 of 7")
- SSE lifecycle event stream per device so UI and agents can subscribe to state changes

### 2.3 Lifecycle Operations
- Create device from template + profile + region
- Start a stopped device
- Stop a running device
- Restart a running device
- Terminate and permanently destroy a device
- All operations are idempotent and resumable — cloud failures mid-operation do not leave devices in permanently broken states

### 2.4 Warm Pools
- Pre-booted device slots per template so a "ready" device is available immediately without provisioning wait time
- Warm pool size configurable per template
- Slot allocation and release tracked as first-class entities
- Warm pool policy (on/off, size) configurable per template; off by default

### 2.5 Resource Tagging
- Every AWS resource created by DeviceLab (EC2 instance, S3 bucket, EBS volume, etc.) is tagged with workspace ID, device ID, template, and created-by so the AWS Cost Explorer shows DeviceLab spending separately

---

## 3. AWS / Cloud Integration

### 3.1 Credential Management
- AWS credential selection: named profile (`~/.aws`), SSO login, or assume-role
- Credentials are never stored by DeviceLab — delegation only
- AWS account identity validation (STS GetCallerIdentity)

### 3.2 Preflight Validation
- Multi-part preflight check runs before any device is created or before bootstrap:
  - Region exists and is enabled
  - IAM permissions exist (policy simulation, not just presence check)
  - Service quotas are not exceeded
  - SSM service reachable
  - EC2 instance type available in region
  - Networking / VPC requirements met
  - AMI / machine image available
- Preflight result is a structured report: each check has a severity (`info` / `warning` / `error`), a human-readable message, and a remediation instruction
- Preflight can be re-run at any time

### 3.3 Bootstrap
- Bootstrap planner shows every AWS resource that will be created and its estimated hourly cost before anything is committed
- Bootstrap creates: IAM role, security group(s), S3 bucket for artifacts, runtime agent pre-staged in S3
- Bootstrap is idempotent — re-running it against an already-bootstrapped account is safe
- Bootstrap status is tracked as a structured model (not completed / in-progress / completed / failed)

### 3.4 AWS Services Used
- **EC2** — virtual machines for Linux, Windows, Android, Mac device families
- **SSM (Systems Manager)** — secure tunnel to running instances; no public inbound ports opened
- **CloudFormation** — infrastructure-as-code for all bootstrap resources
- **Pricing API** — real-time cost data, cached locally with expiration
- **S3** — artifact storage (test outputs, screenshots, recordings, logs)
- **Device Farm** — real iOS device access
- **IAM** — roles, policies, permission simulation

### 3.5 Multi-Account (Post-v1)
- Single AWS account is the v1 requirement
- AssumeRole chain for multi-account support is post-v1

### 3.6 Orphan Detection and Cleanup
- Background polling detects AWS resources tagged by DeviceLab that are no longer tracked in the local database (e.g. created before a crash, never cleaned up)
- Orphans are surfaced in the UI and cost dashboard
- Orphan cleanup can be triggered manually or automatically per policy

---

## 4. Observation (AI Perception)

The observation system is tiered. Cheaper, more structured tiers are always tried first. Escalation requires explicit request or policy.

### 4.1 Tier 1 — Accessibility Tree (AX)
- Structured semantic tree of everything on screen: element type, accessible name, state (enabled/disabled/checked), bounding box
- Equivalent to what a screen reader sees — machine-readable, no pixels required
- Primary default tier for all families that support it

### 4.2 Tier 2 — OCR / Text Index
- Optical character recognition run on the current screen image
- Returns extracted text with positional metadata
- Used when AX is unavailable or insufficient

### 4.3 Tier 3 — Screenshot Metadata
- A still image of the screen with dimensions, format, and capture timestamp
- Available for all families

### 4.4 Tier 4 — VLM / Vision Escalation (Gated)
- Sending the screenshot to a vision language model for interpretation
- Requires user to configure their own API key (BYOK) — never enabled by default
- Cost and latency are surfaced before use

### 4.5 Screen Versioning
- Every screen state change increments a monotonic version number
- Version is included in every observation response
- Agents can request an observation delta (only what changed between version N and N+1) instead of the full tree

### 4.6 Observation Envelopes
- Every observation response is wrapped in a structured envelope containing: capture timestamp, which tier was used, screen version, any warnings (e.g. "AX tree stale, fell back to OCR")

### 4.7 Content Extraction
- Targeted extraction without returning the full tree: text only, headings only, tables only, links only, a specific screen region

### 4.8 Observation Caching
- Observations are cached between requests; the cache is invalidated when the screen version changes

---

## 5. Interaction and Action Execution

### 5.1 Semantic Actions
- Click by accessible name, text anchor, or CSS/XPath selector — not by pixel coordinate
- Type text into a focused or targeted element
- Fill a form field by label or accessible name
- Select an option from a dropdown by label value
- Coordinate-based fallback click when semantic targeting fails

### 5.2 Pointer and Touch
- Mouse move and click (left, right, middle)
- Touch tap, swipe, pinch, long-press for mobile families

### 5.3 Wait Conditions
- Wait until a named element appears on screen
- Wait until a named element disappears
- Wait until a text string appears
- Wait until the screen version changes
- All waits have a configurable timeout and return a structured timeout error if exceeded

### 5.4 Batched Steps — `run_steps`
- Send multiple actions in a single call instead of one per round trip
- Critical for AI agents: reduces token cost and latency of multi-step flows
- Each step in the batch is executed in order
- On partial failure, the response reports exactly which step failed and what the screen looked like at that moment — subsequent steps are not attempted

### 5.5 Screen Version Guards
- Every action can include an `expected_screen_version` field
- If the screen has changed since the agent last observed, the action returns `SCREEN_VERSION_CONFLICT` instead of acting on a stale state
- Prevents acting on the wrong element because the UI changed between observe and act

### 5.6 Evidence Linkage
- Every action stores before-observation and after-observation snapshots
- Every action is assigned a unique evidence ID
- Evidence is queryable by session, recipe run, or device

---

## 6. MCP (Model Context Protocol) Gateway

### 6.1 Transport
- stdio transport for local CLI-based AI agents
- Streamable HTTP transport for remote or web-based AI agents

### 6.2 Capability Handshake
- When an MCP client connects, it receives a capability handshake: the exact set of tools available for the current device family, device state, and client permission role
- No guessing — the agent knows before it tries what will work

### 6.3 Filtered Tool Manifest
- Tool manifest is filtered per session: a browser device does not expose touch tools; a stopped device does not expose interaction tools; an Observe-role client does not see lifecycle tools
- Filtering happens at connection time and is refreshed when device state changes

### 6.4 Permission Roles
- `Observe` — read-only: can observe the screen, list devices, get cost info
- `Interact` — can observe and send actions to the device
- `Test` — can observe, interact, and trigger test runs and recipes
- `Manage` — can observe, interact, test, and control device lifecycle (start/stop/snapshot)
- `Admin` — all of the above plus MCP client management and secret management
- `Dangerous` — destructive or irreversible actions; requires the dangerous mode toggle to be on

### 6.5 Client Management
- Each MCP client has: a registration record, a scoped bearer token, a permission role, rate limits, and a quota
- Token rotation without invalidating the client registration
- Client rate limiting enforced at the gateway

### 6.6 Tool Groups
All tools are organized into named groups. Which groups are available depends on family, state, and role:
- `inventory` — list templates, list devices, list capabilities
- `lifecycle` — create, start, stop, restart, snapshot, fork, terminate
- `observe` — get structured observation, get delta, get screen version, subscribe to changes
- `interact` — click, type, fill, select, wait, run_steps
- `forms` — inspect form structure, validate form state
- `read_content` — extract text, headings, tables, links, regions
- `files` — list artifacts, download artifact, upload artifact
- `network` — network inspection (mitmproxy integration)
- `recipes` — list, run, get run status, record session to recipe
- `subscribe` — lifecycle event subscriptions, observation change subscriptions
- `identity` — request secret reference, acknowledge elicitation
- `cost_safety` — get cost summary, get cap status, get estimate, get guardrail events

---

## 7. Recipes and Automation

### 7.1 Recipe Schema
- YAML format with typed inputs schema
- Metadata: name, version, description, compatible families, required inputs with types and defaults
- Sections: setup steps, action steps, assertions, cleanup steps (cleanup always runs regardless of failure)

### 7.2 Step Types
- Semantic action steps (click, type, fill, wait, run_steps)
- Assertion steps (expect element, expect text, expect screen version)
- Artifact capture steps (screenshot at this point, start recording, stop recording)
- Conditional steps (if/else based on observation result)

### 7.3 Execution
- Recipe execution service runs recipes against a named device
- Typed inputs are injected at run time
- Run state is persisted: step-by-step status, timing, outputs, artifact links
- Run is queryable by ID while in progress and after completion

### 7.4 Recording
- Interact with a device manually through the UI or MCP; DeviceLab records every action and generates a draft recipe YAML
- Draft recipe includes selector stability warnings (flags steps that used fragile coordinate-based fallbacks that may not replay reliably)

### 7.5 Versioning and Reuse
- Recipes are versioned (v1, v2, …)
- Recipes can reference other recipes as sub-steps (composition)
- Smoke test suites and full test suites are defined as ordered collections of recipes

---

## 8. Identity Broker and Secrets

### 8.1 Secret References
- Secrets are never passed directly through the API or MCP — only reference IDs (`SecretRef`) are passed
- The reference ID resolves to the actual value inside the Identity Broker, never exposed to callers

### 8.2 Backends
- **OS keychain** (required baseline): Mac Keychain on macOS, Linux Secret Service (libsecret) on Linux
- **HashiCorp Vault** (optional plugin, post-v1)

### 8.3 Elicitation Flow
- An MCP agent that needs a secret sends an elicitation request
- The request appears in the UI for the human operator to approve or deny
- On approval, the secret is injected into the device session — scoped to that session, recipe run, or client
- The model never receives the plaintext value

### 8.4 Audit and Redaction
- Every secret access (even a successful resolution) is logged as an audit event
- Every API response and log line passes through a redaction pipeline that scrubs values that look like secrets
- Scoped injection: a secret approved for session A cannot be used in session B

---

## 9. Cost Guardrails

### 9.1 Pricing Data
- AWS Pricing API is queried for real per-hour USD prices per service code and attributes
- Prices are cached locally with a configurable expiration (default: 1 hour)
- Conservative estimates are used when exact pricing data is unavailable

### 9.2 Cost Estimates
- Per-device estimated hourly cost is computed before and after creation
- Per-action cost budget is computed for actions that incur AWS charges (snapshots, Device Farm runs, etc.)

### 9.3 Caps and Enforcement
- Workspace-level spending cap (soft and hard)
- **Soft cap**: action proceeds, user sees a visible warning in UI and MCP response
- **Hard cap**: action is blocked and returns `ACTION_UNSAFE` until the cap is raised or resources are freed
- Mac/GPU instance warning gate: explicit confirmation required before creating high-cost instance types regardless of cap status
- Dangerous mode cost blocking: certain operations require dangerous mode to be on before they are even attempted

### 9.4 Cost Visibility
- Cost summary endpoint: current estimated spend this period, cap status, projected spend if all running devices continue
- Cost guardrail event stream: every soft/hard cap trigger is emitted as a structured event
- Orphan resource cost is surfaced separately so users can see exactly what they are paying for ghost machines

---

## 10. Snapshots and Forks

- **Snapshot request** — async: returns immediately with a snapshot ID
- **Snapshot status polling** — poll by snapshot ID to get progress and completion
- **Parent reference** — each snapshot records which device state it was taken from
- **Fork from snapshot** — create a new device starting from an existing snapshot (branching device state)
- **Cleanup on deletion** — when a device is deleted, its associated snapshots are also cleaned up; orphaned EBS volumes and images are not left running
- **Capability-gated** — families that do not support snapshots (e.g. real iOS via Device Farm) return a structured `SNAPSHOT_UNAVAILABLE` error; they do not silently fail

---

## 11. Streaming (Human Sessions)

- **WebRTC media stream** — real-time video of the device screen delivered to the browser; same technology as video calls; negotiated via offer/answer exchange
- **Split input data channel** — keyboard and mouse/touch inputs travel over a separate WebRTC data channel, not muxed with video, for minimum input latency
- **Input latency telemetry** — time-from-keypress-to-device is measured and recorded per session
- **Session reconnect** — if the browser tab closes or the network drops, reconnecting to the same session ID restores the stream without terminating the device
- **Transient network loss resilience** — brief drops (under a configurable threshold) do not trigger session termination

---

## 12. Test Execution and Artifacts

### 12.1 Test Runs
- Test run is a formal entity: created from a device + recipe or test suite, tracked by ID, has a lifecycle (pending / running / passed / failed / error)
- Step-level status: each test case within a run is tracked individually

### 12.2 Artifact Types
- Logs (stdout/stderr from the device or agent)
- Screenshots (point-in-time captures)
- Screen recordings / video (full session or scoped window)
- Network traces (from mitmproxy)
- Test output files (anything the recipe or test writes to disk)

### 12.3 Artifact Format and Delivery
- JUnit XML — default output format, compatible with every CI system (GitHub Actions, Jenkins, CircleCI, etc.)
- Allure-compatible metadata — richer reporting with per-step detail, attachments, and history
- Artifact bundle manifest — a single JSON file listing every artifact in a run with its type, checksum, size, and download URL
- Artifacts are stored in the user's S3 bucket

### 12.4 Integrity and Retention
- Every artifact has a checksum (SHA-256) generated at capture time and verified on retrieval
- Retention policy: configurable per workspace, default 30 days, purge jobs run on schedule

---

## 13. Evidence and Replay

### 13.1 Evidence Records
- Every MCP action generates an evidence record containing: the full request envelope, the full response envelope, the screen version before, the screen version after, the observation delta, and a list of warnings
- Evidence records are keyed by the evidence ID returned in the action response

### 13.2 Audit Log
- Append-only log of every meaningful system event: device lifecycle transitions, recipe executions, secret accesses, cost guardrail triggers, dangerous mode toggles, client token rotations, policy decisions
- Each event is immutable after write
- Each event has a checksum and an immutable server-side timestamp — tamper-evident
- Events are queryable by device, session, client, time range, and event type

### 13.3 Replay Timeline
- API endpoint that returns the complete ordered history of a session or recipe run as a sequence of evidence records
- Each record in the timeline can be expanded to show the full before/after observation, screen version, and action envelope
- Suitable for stepping through exactly what an AI agent did, frame by frame

### 13.4 Trace Correlation
- Every action across MCP gateway, local API, and runtime agent shares a trace ID
- The trace ID is surfaced in the evidence record, the audit log, and the structured logs
- Enables root-cause analysis by following one action across all system layers

### 13.5 Retention
- Evidence records default to 30-day retention
- Purge jobs run on a schedule; purge is soft-delete first (tombstone) then hard delete

---

## 14. Adapter Plugin SPI

### 14.1 Interface Contract
- Versioned formal interface that every device family adapter must implement
- Interface methods: `provision`, `bootstrap`, `observe`, `act`, `stream`, `snapshot`, `upload_artifact`, `cleanup`
- Adapters declare which methods they implement; unimplemented methods return `CAPABILITY_UNSUPPORTED`

### 14.2 Registry and Lifecycle
- Adapters are discovered and loaded at DeviceLab startup
- Duplicate family IDs are a startup error
- Version negotiation: adapter declares min/max DeviceLab version it supports; incompatible adapters are rejected with a clear error message

### 14.3 Capability Declaration
- Each adapter declares exactly what it supports: which lifecycle operations, which observation tiers, which interaction types, whether streaming is supported, whether snapshots are supported
- This declaration feeds the capability handshake and the filtered tool manifest — agents only see what the adapter actually supports

### 14.4 Conformance Test Suite
- A standard test suite that any adapter must pass to be considered conformant
- Tests cover: provision→ready→terminate round trip, observation contract, action contract, cleanup contract, capability declaration accuracy

---

## 15. Security Model

- **Localhost-only default** — the DeviceLab API binds to `127.0.0.1` by default; not reachable from LAN or internet without explicit configuration change
- **Hard BYOC boundary** — no DeviceLab server in the cloud; all traffic is your laptop to your AWS account
- **MCP bearer token authentication** — each AI client has a unique scoped secret token; no unauthenticated tool calls
- **RBAC at manifest level** — tools the client's role doesn't permit are not included in the manifest, so the agent doesn't even know they exist
- **Dangerous mode explicit toggle** — a whole class of destructive actions (terminate all, force-delete, etc.) requires dangerous mode to be on; dangerous mode is off by default; toggling it on is an audit event
- **Confirmation for dangerous operations** — even with dangerous mode on, each dangerous action requires an explicit confirmation field in the request
- **mTLS for gateway ↔ runtime agent** — mutual TLS on the channel between DeviceLab and the agent running on the cloud device; both sides prove their identity
- **SSM tunnel** — runtime communication goes through AWS Systems Manager; no public-facing port is opened on the device
- **No plaintext secrets to model** — hard guarantee; the LLM/agent never receives a plaintext secret value under any code path
- **Output redaction pipeline** — every API response and log line is scanned for patterns that look like secrets and scrubbed before leaving the system
- **Prompt injection filtering** — if text on the device's screen contains instructions trying to redirect the AI agent, DeviceLab's trusted-tool policy detects and filters it before the observation is returned

---

## 16. Error Contract

Every error response has the same shape: `{ code, message, remediation, evidence_id }`. The `evidence_id` points to what was captured at the moment of failure. Defined error codes:

| Code | Meaning |
|---|---|
| `DEVICE_NOT_READY` | Action requires the device to be in `ready` state but it is not |
| `CAPABILITY_UNSUPPORTED` | This device family or state does not support the requested tool |
| `SCREEN_VERSION_CONFLICT` | The screen changed between observation and action; expected version did not match |
| `TARGET_NOT_FOUND` | The semantic target (element name, selector, text anchor) does not exist on the current screen |
| `ACTION_UNSAFE` | A permission check, cost cap, or policy blocked the action |
| `ACTION_TIMEOUT` | A wait condition ran out of time before the condition was met |
| `DEVICE_TEMPLATE_UNSUPPORTED` | The selected template is not available in this region or with this profile |
| `SNAPSHOT_UNAVAILABLE` | This device family or state does not support snapshots |
| `AWS_RATE_LIMITED` | AWS throttled the request; retry semantics are included in the response |

---

## 17. REST API Surface

All endpoints are under `/api/v1/`. Every response follows a consistent shape with a `data` field and optional `error` field.

| Method | Path | Purpose |
|---|---|---|
| GET | `/workspace` | Workspace status, config, and feature flag state |
| GET | `/health` | Liveness and dependency health checks |
| POST | `/cloud-accounts` | Connect an AWS account (store credential reference) |
| POST | `/cloud-accounts/{id}/preflight` | Run preflight validation against the account |
| GET | `/templates` | List available device templates |
| POST | `/devices` | Create a new device |
| GET | `/devices` | List devices with state and cost info |
| GET | `/devices/{id}` | Device detail including current state and phase |
| GET | `/devices/{id}/events` | SSE stream of lifecycle events for a device |
| POST | `/devices/{id}/lifecycle/{action}` | Lifecycle operations: start, stop, restart, terminate |
| GET | `/devices/{id}/stream` | Negotiate a WebRTC streaming session |
| POST | `/devices/{id}/snapshots` | Request a snapshot |
| GET | `/devices/{id}/snapshots/{snap_id}` | Snapshot status |
| POST | `/snapshots/{snap_id}/fork` | Fork a new device from a snapshot |
| POST | `/devices/{id}/recipes/run` | Execute a recipe against a device |
| GET | `/recipes` | List available recipes |
| GET | `/recipes/runs/{run_id}` | Test/recipe run status and step detail |
| GET | `/artifacts` | List artifacts (filterable by device, run, type) |
| GET | `/artifacts/{id}/download` | Download a specific artifact |
| GET | `/cost/summary` | Current spend, cap status, and projection |
| GET | `/audit` | Queryable audit event stream |
| GET | `/replay/{session_id}` | Replay timeline for a session |
| GET | `/mcp/config` | MCP client config block to paste into an AI tool |
| POST | `/mcp/clients/{id}/rotate` | Rotate a client's bearer token |

---

## 18. Web UI

- **First-run onboarding wizard** — step-by-step flow: connect AWS credentials → run preflight → review bootstrap plan → bootstrap → create first device → copy MCP config into AI tool
- **Workspace dashboard** — all devices, their current states, current cost, and cap status at a glance
- **Device creation flow** — template picker, profile picker, region picker, cost preview, confirm
- **Device detail page** — current state, phase sub-steps, lifecycle action buttons, cost
- **Session stream viewer** — live WebRTC video of the device screen with keyboard and mouse input passthrough
- **Cost dashboard** — current spend, hourly rate, hard/soft cap indicators, orphan resource list, projection
- **Artifact browser** — browse and download every file from every test run; filterable by device, run, type, date
- **Replay timeline viewer** — step through an AI agent session action by action; each step shows the before/after screen state and the action envelope
- **Recipe editor** — create or edit a recipe YAML with a structured form; trigger a recipe run
- **MCP client config display** — the exact JSON config block to paste into Cursor, Claude Code, or any MCP-compatible AI tool, with one-click copy
- **Audit log viewer** — browse the immutable event history; filter by event type, device, time range
- **Settings panel** — feature flags, dangerous mode toggle (with confirmation), spending cap configuration, warm pool configuration

---

## 19. Data Entities

| Entity | What it is |
|---|---|
| `Workspace` | Top-level container; one per install by default |
| `CloudAccount` | A connected AWS account with credential reference (not the credential itself) |
| `DeviceTemplate` | A pre-defined device type: image, regions, resource requirements, capability declarations |
| `DeviceProfile` | Sizing and policy settings: instance type, auto-stop timeout, snapshot policy |
| `Device` | A running or stopped cloud device instance |
| `Session` | A period of active interaction with a device |
| `McpClient` | A registered AI agent client with token, role, rate limits |
| `Snapshot` | A saved device state at a point in time |
| `Recipe` | A versioned automation script in YAML |
| `TestRun` | A formal execution of a recipe or test suite against a device |
| `Artifact` | A file produced by a session or test run |
| `Evidence` | The stored before/after record of an MCP action |
| `SecretRef` | A reference to a secret in the keychain (never the value) |
| `CostEstimate` | A pricing record for a device or action |
| `AuditEvent` | An immutable, checksummed log entry |
| `WarmPoolSlot` | A pre-booted device waiting for allocation |

---

## 20. External Integrations

| Integration | What it does in DeviceLab |
|---|---|
| **AWS EC2** | The actual cloud computers for Linux, Windows, Android, Mac families |
| **AWS SSM** | Secure tunnel to reach running instances without opening public ports |
| **AWS CloudFormation** | Infrastructure-as-code for creating bootstrap resources |
| **AWS Pricing API** | Real per-hour cost data for every instance type and service |
| **AWS S3** | User-owned bucket for artifact storage |
| **AWS Device Farm** | Real physical iOS devices in an Amazon data center |
| **Playwright** | Browser automation for the Browser device family |
| **Appium** | Mobile automation framework for Android and iOS |
| **ADB (Android Debug Bridge)** | Standard protocol for communicating with Android devices |
| **mitmproxy (embedded)** | Network proxy inside the device session for inspecting HTTP/HTTPS traffic |
| **coturn (user-owned)** | TURN relay server the user runs themselves for WebRTC when direct connections fail |
| **OS Keychain** | Mac Keychain / Linux Secret Service for local secret storage |
| **OpenTelemetry** | Standard observability format; user provides their own collector endpoint |
| **HashiCorp Vault** | Optional enterprise secret backend (post-v1) |
| **BYOK Vision Providers** | User's own OpenAI / Anthropic / etc. API key for VLM screen interpretation |

---

## 21. Observability and Operations

- Structured JSON logs on every layer: API, MCP gateway, runtime agent
- Redaction rules applied to all log output before writing
- Metrics emitted: request latency, action success rate, observation tier distribution, cost events, device lifecycle durations
- Trace ID correlation across MCP gateway / local API / runtime agent
- OpenTelemetry exporter to user-provided endpoint (Honeycomb, Grafana, Datadog, etc.)
- Health check endpoints: liveness (`/health`) and readiness (checks DB, agent reachability)
- Docker Compose local stack for development
- Traefik production overlay for reverse proxy and TLS termination
- Kubernetes base manifests (optional, for teams running DeviceLab in a shared cluster)
- Alembic database migrations — versioned, incremental, never destructive
- Runbooks for every known failure scenario: API down, database failure, JWT rotation, orphan cleanup, bootstrap rollback

---

## 22. Non-Goals (What DeviceLab Explicitly Will Never Do)

- No DeviceLab-hosted SaaS, no remote accounts, no subscription billing
- No cloud markup — you pay AWS what AWS charges
- No screenshot-loop-first computer use as the primary AI paradigm (structured observation is the default; screenshots are a fallback tier)
- No public inbound ports opened on devices by default
- No proprietary software bundled in the open-source core
- No secrets returned to model context under any circumstances
- No reseller model
