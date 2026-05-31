---
doc_id: "23.12b"
title: "OSS repo candidates — subsystem outsourcing"
section: "Research"
summary: "Enumerated open source GitHub repos whose code or specific modules could be cloned and adapted to save DeviceLab implementation time, organized by subsystem. Includes license flags and exact directories to extract."
updated: "2026-05-30"
---

# OSS Repo Candidates — Subsystem Outsourcing
<!-- research round: 2026-05-30 | method: deep web search + repo fetch verification -->

For each major DeviceLab subsystem, this file enumerates open source GitHub repos whose code (or specific subdirectories) could be cloned and adapted rather than written from scratch. Repos were verified for license and folder structure. A comparison table across candidates per subsystem is a follow-up task.

**License key:**
- ✅ Permissive (MIT / Apache-2.0 / BSD)
- ⚠️ Copyleft (AGPL / LGPL — usable since DeviceLab is OSS, but verify before depending on)

---

## 1. WebRTC Streaming + Split Input Data Channel

**What to outsource:** Peer connection setup, ICE/DTLS/SRTP negotiation, offer/answer signaling, video track management, and the separate data channel for keyboard/mouse input.

### A. `aiortc/aiortc` ✅ BSD-3-Clause
- Python WebRTC + ORTC implementation using asyncio. Handles peer connections, data channels, ICE, DTLS natively — no browser required. 1,300+ commits, actively maintained.
- **Directories to clone:** `src/aiortc/` (core peer connection + data channel), `examples/server/` (complete signaling server over HTTP), `examples/datachannel-cli/` (standalone data channel — maps to DeviceLab's split input channel)
- **Source:** [S051]

### B. `mpromonet/webrtc-streamer` ✅ Apache-2.0
- C++ server designed for streaming device/screen capture sources over WebRTC. Thin HTTP signaling API, easy to wrap from Python. Used in embedded and cloud device streaming products.
- **Directories to clone:** `/src/` (WebRTC signaling handler + stream source abstraction), `/html/` (browser-side JS client — adapt into DeviceLab UI stream viewer)
- **Source:** [S052]

### C. `livekit/livekit` ✅ Apache-2.0
- Production-grade WebRTC SFU (selective forwarding unit) in Go with a Python SDK (`livekit/python-sdks`). Room/participant model, data channels as first-class, reconnect handling at scale.
- **Directories to clone:** `pkg/sfu/` (forwarding logic if self-hosting), `livekit-server-sdk-python/` (Python client for runtime agent + control plane publish/subscribe)
- **Source:** [S053]

---

## 2. MCP Server / Gateway Implementation

**What to outsource:** Tool registration, capability negotiation handshake, stdio and HTTP transports, request routing, per-client permission filtering, and rate limiting.

### A. `modelcontextprotocol/python-sdk` ✅ MIT
- Official Python MCP SDK. `FastMCP` gives decorator-based tool registration; low-level `Server` class exposes `get_capabilities()` for handshake. Both stdio and Streamable HTTP transports built in.
- **Directories to clone:** `src/mcp/server/` (entire server implementation), `src/mcp/server/fastmcp.py` (tool/resource decorators), `src/mcp/server/stdio.py` + `src/mcp/server/sse.py` (transport implementations)
- **Source:** [S023]

### B. `IBM/mcp-context-forge` ✅ Apache-2.0
- Full MCP gateway/proxy with RBAC, rate limiting, audit trails, and federation. 7,000+ tests. Maps directly to DeviceLab's multi-client MCP gateway with per-client permission scoping.
- **Directories to clone:** `mcpgateway/services/` (business logic — tool routing, auth, rate limiting), `mcpgateway/routers/` (HTTP endpoint definitions), `mcpgateway/plugins/` (plugin registration pattern — maps to adapter SPI)
- **Source:** [S054]

### C. `microsoft/playwright-mcp` ✅ Apache-2.0
- Production MCP server for browser automation. 60+ tools gated by `--caps` flag — the best real-world example of filtered tool manifests and accessibility-snapshot-as-observation.
- **Directories to clone:** `src/tools/` (individual tool implementations — each shows observe → validate → act → return structured result), `src/snapshot.ts` (AX tree walker and serializer)
- **Source:** [S025]

---

## 3. Browser Automation / Device Family Adapter

**What to outsource:** Browser process lifecycle, session management (persistent state, cookies, reconnect), and serialization of browser state into structured observation envelopes.

### A. `steel-dev/steel-browser` ✅ Apache-2.0
- Batteries-included browser session API for AI agents. Manages browser processes and sessions (state, cookies, storage) over REST. TypeScript — port or wrap.
- **Directories to clone:** `/api/` (session CRUD, browser process lifecycle, `/sessions` endpoint + reconnect/reset semantics), `/api/src/services/` (session manager service — maps to DeviceLab Browser family adapter)
- **Source:** [S055]

### B. `browser-use/browser-use` ✅ MIT
- Python-native AI browser agent framework on top of Playwright. Cleanest Python implementation of AX-tree-from-browser extraction and action execution.
- **Directories to clone:** `browser_use/browser/` (Playwright session wrapper + state management), `browser_use/dom/` (DOM/AX tree extraction + element resolution), `browser_use/controller/` (action execution service — maps to Browser family `act()`)
- **Source:** [S056]

### C. `microsoft/playwright-mcp` ✅ Apache-2.0 *(dual-listed — see §2)*
- The AX snapshot serialization is directly usable as DeviceLab's Tier 1 observation format for the Browser family.
- **Directories to clone:** `src/tools/` (per-tool action patterns), `src/snapshot.ts` (raw AX tree walker)

---

## 4. Android Device Control (ADB + Appium + Accessibility Tree)

**What to outsource:** ADB connection management, UIAutomator2 accessibility tree extraction, action execution on Android, and accessibility snapshot generation.

### A. `callstackincubator/agent-device` ✅ MIT
- Purpose-built CLI for AI agents to control iOS and Android. `android-snapshot-helper` generates compact AX snapshots with interactive refs; `android-adb` exposes ADB as a typed provider contract.
- **Directories to clone:** `src/` (core device provider interface + session management), `android-snapshot-helper/` (AX snapshot generator — DeviceLab Android Tier 1 observation), `android-adb/` (ADB wrapper: logcat, keyboard, clipboard, app helpers, port reverse)
- **Source:** [S057]

### B. `appium/appium-uiautomator2-driver` ✅ Apache-2.0
- Production Appium driver for Android UIAutomator2. Most battle-tested Android AX extraction and action execution code in open source; millions of CI runs depend on it.
- **Directories to clone:** `lib/driver.js` (session lifecycle — createSession/deleteSession), `lib/commands/` (action implementations: click, type, scroll, swipe, getPageSource for AX tree), `lib/uiautomator2.js` (UiAutomator2 server communication)
- **Source:** [S058]

### C. `appium/appium-adb` ✅ Apache-2.0
- Standalone ADB wrapper used by Appium internally. Every ADB capability (shell, install, uninstall, input, screencap, logcat) as typed async functions.
- **Directories to clone:** `lib/` (full ADB client — `adb.js` for core commands, `lib/tools/` for shell/app management helpers)
- **Source:** [S059]

### D. `shamanec/GADS` ⚠️ AGPL-3.0
- Self-hosted mobile device farm — architecturally the closest to DeviceLab's Android provider. Hub/provider split, ADB tunnel, Appium integration. AGPL: usable since DeviceLab is OSS but copyleft propagates to modifications.
- **Directories to clone:** `provider/` (device setup + lifecycle management), `client/adb/` (ADB tunnel implementation)
- **Source:** [S060]

---

## 5. AWS Provisioning and Lifecycle Orchestration

**What to outsource:** Preflight validation (IAM simulation, quota checks, region validation), CloudFormation stack management, EC2 lifecycle, SSM session establishment, and resource tagging.

### A. `cloud-custodian/cloud-custodian` ✅ Apache-2.0
- Most mature open-source AWS resource policy engine. YAML-driven policies for every AWS resource type. Production-proven EC2 querying, tag enforcement, quota checking, and lifecycle actions.
- **Directories to clone:** `c7n/resources/ec2.py` (EC2 filters + lifecycle actions — preflight and lifecycle logic), `c7n/resources/ssm.py` (SSM resource management), `c7n/tags.py` (tag enforcement — maps to cost allocation tagging), `c7n/policy.py` (policy execution engine pattern — adapt for guardrail model)
- **Source:** [S061]

### B. `aws-cloudformation/cloudformation-cli-python-plugin` ✅ Apache-2.0
- AWS's own Python plugin for CloudFormation resource providers. Clean patterns for idempotent stack operations, progress tracking, and CloudFormation error handling — exactly what bootstrap needs.
- **Directories to clone:** `python/cloudformation/` (handler invocation model + progress event tracking), `python/cloudformation/exceptions.py` (typed CloudFormation exception hierarchy)
- **Source:** [S062]

### C. `lyft/awspricing` ✅ Apache-2.0
- Python library for the AWS Pricing List API. EC2 pricing helpers, SKU resolution by instance type/region/OS, on-demand and reserved lookups, local caching.
- **Directories to clone:** `awspricing/` (full package — `ec2.py`, `offer.py` for pricing document fetcher + cache, `utils.py` for caching layer)
- **Source:** [S063]

---

## 6. Cloud Runtime Agent (On-Device Process)

**What to outsource:** The agent-side execution loop — receives commands from the control plane, executes observations/actions, streams results back, uploads artifacts, emits lifecycle events.

### A. `agentscope-ai/agentscope-runtime` ✅ Apache-2.0
- Production-ready agent execution runtime with secure sandboxing, resumable command execution, and artifact tracking. The execution loop and sandboxing model are directly adaptable.
- **Directories to clone:** `agentscope_runtime/executor/` (command execution with resume semantics), `agentscope_runtime/sandbox/` (isolation + security boundary), `agentscope_runtime/artifacts/` (artifact collection + upload pipeline)
- **Source:** [S064]

### B. `openstf/stf` ✅ Apache-2.0
- Original Smartphone Test Farm. The `lib/units/device/` component is architecturally the closest existing thing to DeviceLab's runtime agent: runs on/near the device, bridges ADB, handles streaming via minicap/minitouch, communicates with hub over ZMQ. Node.js — architecture translates.
- **Directories to clone:** `lib/units/device/` (device-side agent unit — lifecycle, streaming bridge, command dispatch), `lib/units/provider/` (provider process that manages multiple device agents — maps to runtime agent supervisor)
- **Source:** [S065]

---

## 7. Structured Observation / Accessibility Tree Extraction

**What to outsource:** Platform-specific AX tree extraction (macOS Accessibility API, Windows UIA, Linux AT-SPI). Each is a significant native integration.

### A. `viralmind-ai/accessibility-tree-parsers` ✅ MIT
- Platform-specific AX tree parsers for Windows (UIA), macOS (native Accessibility framework), and Linux (GNOME AT-SPI2). All output the same JSON schema: `{name, role, description, value, bounds, children}`. Exactly Tier 1 observation.
- **Directories to clone:** `linux-ax/` (Linux AT-SPI GJS parser), `mac-ax/` (macOS Accessibility Python parser), `win-ax/` (Windows UIA Python parser)
- **Source:** [S066]

### B. `Topdu/OpenOCR` ✅ Apache-2.0
- Commercial-grade OCR + document parsing toolkit. Tier 2 observation (OCR fallback). Includes text detection, recognition, layout analysis, and table extraction — maps to DeviceLab's content extraction tools.
- **Directories to clone:** `openocr/text_det/` (text detection), `openocr/text_rec/` (text recognition), `openocr/table/` (table structure extraction — maps to "extract tables" content tool)
- **Source:** [S067]

### C. `browser-use/browser-use` ✅ MIT *(dual-listed — see §3)*
- `browser_use/dom/` has a clean implementation of converting live browser DOM into a compact indexed representation with stable refs — maps to DeviceLab's screen version + delta observation model.
- **Directories to clone:** `browser_use/dom/` (DOM indexing + ref generation), `browser_use/dom/history_tree_processor/` (delta/diff computation between DOM states)

---

## 8. Recipe / Automation DSL Execution Engine

**What to outsource:** YAML step parser, step execution loop, assertion evaluation, conditional branching, variable injection, and error/cleanup handling.

### A. `pypyr/pypyr` ✅ Apache-2.0
- Python-native YAML pipeline executor. Step modules are Python callables; executor handles loops, conditionals, error handling, variable substitution, retry. Clean plugin model for custom step types.
- **Directories to clone:** `pypyr/` (full core — `pypyr/parser/` for YAML parsing, `pypyr/steps/` for built-in step types to model DeviceLab action steps after, `pypyr/errors.py` for step failure taxonomy, `pypyr/context.py` for variable/context injection)
- **Source:** [S068]

### B. `monoscope-tech/testkit` ✅ MIT
- YAML-based DSL for API and browser automation testing. Has assertion syntax and value capture from response for use in subsequent steps — exactly the recipe assertion and chained-input pattern.
- **Directories to clone:** `src/` (step schema + executor), `src/assertions/` (assertion evaluation engine), `src/capture/` (value extraction + variable binding between steps)
- **Source:** [S069]

### C. `pmarkert/hyperpotamus` ✅ MIT
- YAML/JSON scripting engine with capture, assertion, and multi-step sequencing. Small and embeddable. The capture-for-next-step pattern is directly useful for recipe variable chaining.
- **Directories to clone:** `lib/pipeline.js` (step sequencing), `lib/actions/` (action type registry), `lib/matchers/` (assertion matchers)
- **Source:** [S070]

---

## 9. Cost Guardrails and AWS Pricing

**What to outsource:** AWS Pricing API client, price lookup and caching, budget tracking, and policy-based enforcement (block/warn on cap breach).

### A. `lyft/awspricing` ✅ Apache-2.0 *(dual-listed — see §5)*
- Cleanest Python AWS Pricing API wrapper. SKU resolution, on-demand/reserved lookups, local caching.
- **Directories to clone:** `awspricing/` (full package — `ec2.py`, `offer.py`, `utils.py`)

### B. `cloud-custodian/cloud-custodian` ✅ Apache-2.0 *(dual-listed — see §5)*
- Policy actions model with `mark`, `stop`, `terminate` lifecycle gates — adaptable to soft/hard cap enforcement.
- **Directories to clone:** `c7n/actions/core.py` (policy action base + enforcement model), `c7n/filters/cost.py` (cost-based resource filtering), `c7n/resources/ec2.py` (EC2 cost actions)

### C. `project-koku/koku` ⚠️ LGPL-3.0
- Red Hat's cloud cost management platform. Production-proven AWS cost report ingestion, storage, and aggregation. Extractable AWS modules.
- **Directories to clone:** `koku/providers/aws/` (AWS cost report parser + ingester), `koku/cost_models/` (cost model + rate calculation — adapt as DeviceLab's CostEstimate entity logic)
- **Source:** [S071]

---

## 10. Evidence / Audit Log System

**What to outsource:** Append-only event storage, SHA-256 hash chaining (each event includes hash of previous), checksummed timestamps, tamper-detection on read.

### A. `google/trillian` ✅ Apache-2.0
- Google's production append-only, cryptographically verifiable log — used in Certificate Transparency. Gold standard for tamper-evident logs. Merkle tree proofs, inclusion proofs, clean log API. Go.
- **Directories to clone:** `core/` (Merkle tree + log entry hashing — port hash-chain logic to Python), `merkle/` (Merkle tree for inclusion proofs)
- **Source:** [S072]

### B. `AuditKitDev/auditkit` ⚠️ AGPL-3.0 *(commercial license available separately)*
- Cleanest ready-to-use SHA-256 hash chaining + Merkle tree proofs with Python SDK. AGPL: since DeviceLab is OSS this is likely fine — confirm.
- **Directories to clone:** `packages/sdk-python/` (Python client with event submission + chain verification), `apps/api/` (study append-only storage model + hash-chain generation; re-implement in FastAPI)
- **Source:** [S073]

### C. `lulzasaur9192/agent-audit-log-examples` ✅ MIT
- Minimal HMAC-SHA256 hash-chained audit log in Python. Small enough to read in full and lift directly. Each event: `{id, timestamp, payload, hmac, prev_hmac}`.
- **Directories to clone:** `python/` (core log implementation — expand into DeviceLab's `AuditEvent` entity model)
- **Source:** [S074]

### D. `Jreamr/ai-action-ledger` ✅ MIT
- Tamper-evident audit log designed specifically for AI agent actions — the exact use case of DeviceLab's evidence + replay system.
- **Directories to clone:** Core log implementation files for hash-chain and entry serialization
- **Source:** [S075]

---

## 11. Secret / Credential Management

**What to outsource:** OS keychain backend abstraction, credential storage/retrieval interface, headless Linux keyring support.

### A. `jaraco/keyring` ✅ MIT
- Canonical Python keyring library. Backends for macOS Keychain, Linux Secret Service (GNOME/KDE), and Windows Credential Locker. `KeyringBackend` base class is the exact interface DeviceLab's Identity Broker wraps.
- **Directories to clone:** `keyring/backend.py` (backend interface that IdentityBroker wraps), `keyring/backends/` (platform-specific implementations to include as-is), `keyring/errors.py` (credential error taxonomy)
- **Source:** [S076]

### B. `infisical/infisical` ✅ MIT
- Full open-source self-hostable secret management platform. The Python SDK is the integration path for users who want a Vault-like alternative backend.
- **Directories to clone:** `cli/packages/` (CLI secret injection patterns — maps to DeviceLab's elicitation-gated injection flow), `backend/src/services/secret/` (secret reference resolution service — architecture reference for `SecretRef` entity)
- **Source:** [S077]

### C. `open-source-cooperative/keyring-core` ✅ MIT/Apache
- Cross-platform Rust library for credential management. `secret-service` and `file` backends work headlessly — relevant for the runtime agent on Linux EC2 without a desktop keyring daemon.
- **Directories to clone:** `src/` (backend trait definitions + platform implementations — reference for headless-Linux keyring strategy)
- **Source:** [S078]

---

## 12. Network Inspection Proxy (mitmproxy Embedding)

**What to outsource:** HTTP/HTTPS intercepting proxy, addon/hook system for flow capture, embedded usage mode (running as a library inside the runtime agent).

### A. `mitmproxy/mitmproxy` ✅ MIT
- The canonical choice. MIT license, Python-native, designed to be embedded as a library. Addon API gives `request`, `response`, `tls_start`, `websocket_message` hooks.
- **Directories to clone:** `mitmproxy/addons/` (built-in addons as reference for DeviceLab's flow-capture addon), `mitmproxy/proxy/` (proxy engine — for embedded mode), `examples/contrib/` (embedded usage examples — `web_scanner.py` + `io_write_flow.py` show how to run mitmproxy programmatically), `mitmproxy/io/` (flow serialization to HAR/binary — maps to network trace artifact type)
- **Source:** [S079]

### B. `mitmproxy/mitmproxy_rs` ✅ MIT
- Rust core of mitmproxy. WireGuard mode (proxy any device configured as WireGuard client) and Local Redirect mode (proxy by process name/PID). Relevant for non-browser device families where you cannot inject a proxy certificate.
- **Directories to clone:** `src/` (WireGuard mode implementation — reference for transparent proxy strategy for mobile/desktop families)
- **Source:** [S080]

---

## Full License Summary

| Subsystem | Repo | License |
|---|---|---|
| WebRTC streaming | `aiortc/aiortc` | ✅ BSD-3 |
| WebRTC streaming | `mpromonet/webrtc-streamer` | ✅ Apache-2.0 |
| WebRTC streaming | `livekit/livekit` | ✅ Apache-2.0 |
| MCP gateway | `modelcontextprotocol/python-sdk` | ✅ MIT |
| MCP gateway | `IBM/mcp-context-forge` | ✅ Apache-2.0 |
| MCP gateway | `microsoft/playwright-mcp` | ✅ Apache-2.0 |
| Browser adapter | `steel-dev/steel-browser` | ✅ Apache-2.0 |
| Browser adapter | `browser-use/browser-use` | ✅ MIT |
| Android control | `callstackincubator/agent-device` | ✅ MIT |
| Android control | `appium/appium-uiautomator2-driver` | ✅ Apache-2.0 |
| Android control | `appium/appium-adb` | ✅ Apache-2.0 |
| Android control | `shamanec/GADS` | ⚠️ AGPL-3.0 |
| AWS provisioning | `cloud-custodian/cloud-custodian` | ✅ Apache-2.0 |
| AWS provisioning | `lyft/awspricing` | ✅ Apache-2.0 |
| AWS provisioning | `cloudformation-cli-python-plugin` | ✅ Apache-2.0 |
| Runtime agent | `agentscope-ai/agentscope-runtime` | ✅ Apache-2.0 |
| Runtime agent | `openstf/stf` | ✅ Apache-2.0 |
| AX tree extraction | `viralmind-ai/accessibility-tree-parsers` | ✅ MIT |
| AX tree extraction | `Topdu/OpenOCR` | ✅ Apache-2.0 |
| AX tree extraction | `browser-use/browser-use` | ✅ MIT |
| Recipe DSL | `pypyr/pypyr` | ✅ Apache-2.0 |
| Recipe DSL | `monoscope-tech/testkit` | ✅ MIT |
| Recipe DSL | `pmarkert/hyperpotamus` | ✅ MIT |
| Cost guardrails | `lyft/awspricing` | ✅ Apache-2.0 |
| Cost guardrails | `cloud-custodian/cloud-custodian` | ✅ Apache-2.0 |
| Cost guardrails | `project-koku/koku` | ⚠️ LGPL-3.0 |
| Audit log | `google/trillian` | ✅ Apache-2.0 |
| Audit log | `AuditKitDev/auditkit` | ⚠️ AGPL-3.0 |
| Audit log | `lulzasaur9192/agent-audit-log-examples` | ✅ MIT |
| Audit log | `Jreamr/ai-action-ledger` | ✅ MIT |
| Secrets | `jaraco/keyring` | ✅ MIT |
| Secrets | `infisical/infisical` | ✅ MIT |
| Secrets | `open-source-cooperative/keyring-core` | ✅ MIT |
| Network proxy | `mitmproxy/mitmproxy` | ✅ MIT |
| Network proxy | `mitmproxy/mitmproxy_rs` | ✅ MIT |

---

## Comparison Tables — Per Subsystem

Criteria scored 1–3 (3 = best):

- **Fit** — how closely the repo's architecture matches what DeviceLab needs (1 = needs heavy adaptation, 3 = drop-in or near-drop-in)
- **Extractability** — how cleanly a subdirectory can be lifted without pulling in the whole repo as a dependency (1 = tightly coupled, 3 = module is self-contained)
- **Maintenance** — repo health: commit frequency, open issues, release cadence (1 = stale/uncertain, 3 = actively maintained)
- **License risk** — permissive = 3, LGPL = 2, AGPL = 1
- **Python-native** — whether the extractable part is Python (3), has Python bindings (2), or is another language requiring a wrapper (1)

**Recommendation** is the pick for DeviceLab's first integration pass.

---

### 1. WebRTC Streaming + Split Input Data Channel

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `aiortc/aiortc` | 3 | 3 | 3 | 3 | 3 | **15** | Pure Python asyncio — `examples/datachannel-cli` is almost exactly the split input channel pattern |
| `mpromonet/webrtc-streamer` | 2 | 2 | 2 | 3 | 1 | **10** | C++ — needs a Python wrapper; good for the media server side but adds a native build step |
| `livekit/livekit` | 2 | 1 | 3 | 3 | 2 | **11** | Go server + Python SDK; better fit for a managed SFU topology, overkill if DeviceLab self-routes |

**Recommendation: `aiortc/aiortc`** — pure Python, BSD-3, actively maintained, `src/aiortc/` + `examples/server/` + `examples/datachannel-cli/` covers both media and split input channel with minimal adaptation. Use LiveKit as a fallback if scale demands an SFU.

---

### 2. MCP Server / Gateway Implementation

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `modelcontextprotocol/python-sdk` | 3 | 3 | 3 | 3 | 3 | **15** | Official SDK — this is the protocol, not just a wrapper. `src/mcp/server/` is exactly DeviceLab's MCP layer |
| `IBM/mcp-context-forge` | 2 | 2 | 3 | 3 | 3 | **13** | Adds gateway-level RBAC, rate limiting, federation — valuable for the multi-client permission layer but heavier to extract |
| `microsoft/playwright-mcp` | 2 | 2 | 3 | 3 | 1 | **11** | TypeScript — useful as an architecture reference and for porting the filtered tool manifest pattern, not a direct clone |

**Recommendation: `modelcontextprotocol/python-sdk`** as the foundation (non-negotiable — it's the protocol implementation). Layer `IBM/mcp-context-forge`'s `mcpgateway/services/` patterns on top for the per-client RBAC and rate-limiting middleware that DeviceLab's gateway needs beyond the base SDK.

---

### 3. Browser Automation / Device Family Adapter

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `steel-dev/steel-browser` | 3 | 2 | 3 | 3 | 1 | **12** | TypeScript — session management architecture is the best match for DeviceLab's Browser adapter, but needs porting |
| `browser-use/browser-use` | 3 | 3 | 3 | 3 | 3 | **15** | Python, MIT — `browser_use/browser/` + `browser_use/dom/` + `browser_use/controller/` maps directly to the three layers DeviceLab needs |
| `microsoft/playwright-mcp` | 2 | 2 | 3 | 3 | 1 | **11** | TypeScript — best reference for tool-per-action patterns and AX snapshot format; port the patterns not the code |

**Recommendation: `browser-use/browser-use`** — Python-native, MIT, actively maintained, and the three subdirectories (`browser/`, `dom/`, `controller/`) map cleanly onto DeviceLab's Browser family adapter interfaces. Reference `steel-dev/steel-browser` for session lifecycle design decisions and `playwright-mcp` for AX snapshot serialization format.

---

### 4. Android Device Control

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `callstackincubator/agent-device` | 3 | 3 | 2 | 3 | 1 | **12** | TypeScript/Swift — but `android-snapshot-helper` and `android-adb` map almost perfectly to DeviceLab's Android Tier 1 observation + ADB provider; port or wrap |
| `appium/appium-uiautomator2-driver` | 3 | 2 | 3 | 3 | 1 | **12** | Node.js — most battle-tested Android AX + action execution code in OSS; `lib/commands/` is the reference for every Android action DeviceLab needs to implement |
| `appium/appium-adb` | 3 | 3 | 3 | 3 | 1 | **13** | Node.js but wraps native `adb` binary — can call via subprocess from Python; cleanest ADB abstraction available |
| `shamanec/GADS` | 2 | 2 | 2 | 1 | 2 | **9** | AGPL-3.0 — architecture reference only; `provider/` shows the hub/agent split but copyleft risk means don't copy code |

**Recommendation:** Use `appium/appium-adb` for the ADB layer (call via subprocess or wrap in Python), `appium/appium-uiautomator2-driver`'s `lib/commands/` as the reference implementation for every Android action, and `callstackincubator/agent-device`'s `android-snapshot-helper` as the AX snapshot format reference. GADS is architecture-reference only — don't copy code.

---

### 5. AWS Provisioning and Lifecycle Orchestration

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `cloud-custodian/cloud-custodian` | 3 | 2 | 3 | 3 | 3 | **14** | Python, Apache — `c7n/resources/ec2.py` and `c7n/tags.py` are the most complete open-source EC2 lifecycle + tagging implementations; extracting without the policy runtime takes some work |
| `lyft/awspricing` | 3 | 3 | 2 | 3 | 3 | **14** | Python, self-contained — drop the `awspricing/` package straight in; does one thing well (pricing lookup + cache) |
| `cloudformation-cli-python-plugin` | 2 | 3 | 2 | 3 | 3 | **13** | Python — the progress event tracking and idempotent handler patterns are directly copyable for bootstrap; narrower scope than the others |

**Recommendation:** `lyft/awspricing` for the pricing layer (self-contained, drop-in). `cloud-custodian`'s `c7n/resources/ec2.py` + `c7n/tags.py` as the reference implementation for EC2 lifecycle and tagging — extract the filter and action classes, leave the policy runtime behind. `cloudformation-cli-python-plugin` for bootstrap progress tracking patterns.

---

### 6. Cloud Runtime Agent (On-Device Process)

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `agentscope-ai/agentscope-runtime` | 2 | 2 | 3 | 3 | 3 | **13** | Python — execution loop and sandbox model are adaptable but it's an AI agent runtime, not a device agent; needs significant repurposing |
| `openstf/stf` | 3 | 2 | 1 | 3 | 1 | **10** | Node.js, last major update 2017 — `lib/units/device/` is the architecturally closest thing to DeviceLab's runtime agent but the codebase is old and JS |

**Recommendation:** Neither is a direct clone for this subsystem — the on-device runtime agent is genuinely novel. Use `openstf/stf`'s `lib/units/device/` and `lib/units/provider/` as the **architecture reference** for the hub↔agent communication model and the device-side command dispatch loop. Use `agentscope-runtime`'s `executor/` as the **execution model reference** for resumable commands and artifact upload. This subsystem likely needs to be written from scratch with these as guides.

---

### 7. Structured Observation / Accessibility Tree Extraction

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `viralmind-ai/accessibility-tree-parsers` | 3 | 3 | 2 | 3 | 3 | **14** | Python/GJS — three small self-contained scripts (linux-ax, mac-ax, win-ax) that output the exact JSON schema DeviceLab needs for Tier 1 observation |
| `Topdu/OpenOCR` | 3 | 2 | 3 | 3 | 3 | **14** | Python — commercial-grade OCR + table extraction for Tier 2; `openocr/text_det/` + `openocr/text_rec/` + `openocr/table/` are the three modules DeviceLab needs |
| `browser-use/browser-use` | 2 | 3 | 3 | 3 | 3 | **14** | Python — `browser_use/dom/` delta computation is the best open-source implementation of the screen-version + diff pattern; browser-specific but the concept ports to all families |

**Recommendation:** `viralmind-ai/accessibility-tree-parsers` for Tier 1 desktop AX observation (all three platform scripts). `Topdu/OpenOCR` for Tier 2 OCR fallback. `browser-use/browser-use`'s `dom/history_tree_processor/` as the reference for the screen-version delta algorithm. These three together cover the full observation pyramid for non-browser families.

---

### 8. Recipe / Automation DSL Execution Engine

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `pypyr/pypyr` | 3 | 3 | 3 | 3 | 3 | **15** | Python, Apache — `pypyr/` is a complete step execution engine with conditionals, loops, variable substitution, and a clean plugin model for custom step types. Best fit. |
| `monoscope-tech/testkit` | 2 | 2 | 2 | 3 | 1 | **10** | TypeScript — assertion syntax and value capture are good references but need porting; narrower than pypyr |
| `pmarkert/hyperpotamus` | 2 | 2 | 1 | 3 | 1 | **9** | Node.js, low recent activity — capture/assertion pattern is a useful reference but pypyr covers the same ground in Python with better maintenance |

**Recommendation: `pypyr/pypyr`** — the clearest win in this category. The `pypyr/` package is exactly a YAML step executor with the semantics DeviceLab needs. Clone `pypyr/steps/` as the model for DeviceLab's action step types and `pypyr/context.py` for the typed-inputs injection model. Reference `monoscope-tech/testkit` for assertion DSL syntax design only.

---

### 9. Cost Guardrails and AWS Pricing

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `lyft/awspricing` | 3 | 3 | 2 | 3 | 3 | **14** | Python, self-contained — pricing lookup + cache is exactly what DeviceLab needs; drop in as-is |
| `cloud-custodian/cloud-custodian` | 2 | 2 | 3 | 3 | 3 | **13** | Python — policy enforcement patterns in `c7n/actions/core.py` are the best model for soft/hard cap enforcement; extracting them from the policy runtime takes work |
| `project-koku/koku` | 1 | 1 | 2 | 2 | 3 | **9** | LGPL, heavy Django dependency — `koku/providers/aws/` is interesting for cost report ingestion but the framework overhead makes extraction hard; reference only |

**Recommendation: `lyft/awspricing`** for the pricing data layer (same as §5). `cloud-custodian`'s enforcement action patterns as the design reference for soft/hard cap implementation. Koku is too heavy to extract from — reference the cost aggregation concepts only.

---

### 10. Evidence / Audit Log System

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `google/trillian` | 2 | 1 | 3 | 3 | 1 | **10** | Go — the gold-standard architecture reference for append-only cryptographic logs; extracting the Merkle tree logic into Python is meaningful work but the concepts are clear |
| `AuditKitDev/auditkit` | 3 | 2 | 2 | 1 | 2 | **10** | AGPL — best ready-to-use implementation with Python SDK; copyleft risk is the blocker unless DeviceLab explicitly adopts it as a dependency |
| `lulzasaur9192/agent-audit-log-examples` | 2 | 3 | 1 | 3 | 3 | **12** | Python, MIT — minimal but directly portable HMAC-SHA256 hash chain; small enough to read in full and expand into DeviceLab's full AuditEvent model |
| `Jreamr/ai-action-ledger` | 3 | 3 | 1 | 3 | 3 | **13** | Python, MIT — purpose-built for AI agent action ledgers; small and directly relevant; maintenance status uncertain |

**Recommendation: `lulzasaur9192/agent-audit-log-examples`** as the implementation seed (MIT, Python, minimal — port the `python/` HMAC-SHA256 chain directly into DeviceLab's `AuditEvent` model and expand). Use `google/trillian`'s `merkle/` as the architecture reference if Merkle inclusion proofs are needed later. Avoid AuditKit unless the AGPL is explicitly reviewed and accepted.

---

### 11. Secret / Credential Management

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `jaraco/keyring` | 3 | 3 | 3 | 3 | 3 | **15** | Python, MIT — this is essentially the standard library for this problem; `keyring/backends/` covers Mac/Linux/Windows as-is; `KeyringBackend` is the exact interface DeviceLab's IdentityBroker wraps |
| `infisical/infisical` | 2 | 2 | 3 | 3 | 2 | **12** | Full platform — too large to clone from, but the Python SDK is the right integration path for users who want Vault-like secret management; use as a plugin backend target |
| `open-source-cooperative/keyring-core` | 2 | 2 | 2 | 3 | 1 | **10** | Rust — relevant for headless Linux runtime agent scenarios where there's no desktop keyring daemon; port the `secret-service` headless pattern to Python |

**Recommendation: `jaraco/keyring`** — install as a direct dependency, don't clone. It's the standard Python keyring library and covers all three platforms. `infisical/infisical`'s Python SDK is the Vault-alternative backend integration path (post-v1). `keyring-core`'s headless approach is the reference for the runtime agent on Linux EC2.

---

### 12. Network Inspection Proxy

| Repo | Fit | Extractability | Maintenance | License risk | Python-native | Total | Notes |
|---|---|---|---|---|---|---|---|
| `mitmproxy/mitmproxy` | 3 | 3 | 3 | 3 | 3 | **15** | Python, MIT — designed to be embedded as a library; `mitmproxy/addons/` is the exact plugin model DeviceLab needs for flow capture; `examples/contrib/` shows embedded usage |
| `mitmproxy/mitmproxy_rs` | 2 | 2 | 3 | 3 | 2 | **12** | Rust with Python bindings — WireGuard transparent proxy mode is the right approach for mobile/desktop families that can't have a certificate injected; use alongside mitmproxy proper |

**Recommendation: `mitmproxy/mitmproxy`** — install as a direct dependency and write a DeviceLab-specific addon. Clone `mitmproxy/addons/export.py` as the template for the flow-to-artifact serializer and `examples/contrib/` for the embedded process pattern. Add `mitmproxy_rs` for transparent proxy support on non-browser device families.

---

## Master Recommendation Summary

| Subsystem | Primary pick | Role | Secondary |
|---|---|---|---|
| WebRTC streaming | `aiortc/aiortc` | Clone `src/aiortc/` + examples | `livekit` if SFU scale needed |
| MCP gateway | `modelcontextprotocol/python-sdk` | Direct dependency (foundation) | `IBM/mcp-context-forge` patterns for RBAC layer |
| Browser adapter | `browser-use/browser-use` | Clone `browser_use/browser/` + `dom/` + `controller/` | `steel-dev/steel-browser` for session design reference |
| Android control | `appium/appium-adb` | Subprocess wrapper | `appium-uiautomator2-driver` as action reference |
| AWS provisioning | `lyft/awspricing` | Direct dependency (pricing) | `cloud-custodian` for EC2 lifecycle patterns |
| Runtime agent | Write from scratch | Use STF + agentscope as architecture references | — |
| AX tree extraction | `viralmind-ai/accessibility-tree-parsers` | Clone all three platform scripts | `OpenOCR` for Tier 2 OCR |
| Recipe DSL | `pypyr/pypyr` | Clone `pypyr/` core | `testkit` for assertion DSL reference |
| Cost guardrails | `lyft/awspricing` | Direct dependency (same as AWS provisioning) | `cloud-custodian` enforcement patterns |
| Audit log | `lulzasaur9192/agent-audit-log-examples` | Port `python/` hash chain | `google/trillian` for Merkle proofs reference |
| Secrets | `jaraco/keyring` | Direct dependency | `infisical` SDK as Vault-alternative backend |
| Network proxy | `mitmproxy/mitmproxy` | Direct dependency + custom addon | `mitmproxy_rs` for transparent proxy |

---

---

## Final Decisions — Locked

These are the definitive picks. No longer open for comparison — these are what gets built against.

### Subsystem decisions

| Subsystem | Decision | How to integrate | Reject |
|---|---|---|---|
| **WebRTC streaming** | `aiortc/aiortc` | `pip install aiortc` — wrap `src/aiortc/` peer connection + data channel classes directly; adapt `examples/server/` as the signaling endpoint | `mpromonet` (C++ build overhead), `livekit` (SFU overkill for v1) |
| **MCP gateway** | `modelcontextprotocol/python-sdk` | `pip install mcp` — use `FastMCP` as the server base; implement per-device tool filtering in DeviceLab middleware on top | `IBM/mcp-context-forge` (too heavy to extract; steal RBAC patterns only) |
| **Browser adapter** | `browser-use/browser-use` | `pip install browser-use` — use `browser_use/browser/` session wrapper + `browser_use/dom/` AX extraction directly; `browser_use/controller/` as action execution model | `steel-dev` (TypeScript port cost), `playwright-mcp` (TypeScript, patterns-only reference) |
| **Android control** | `appium/appium-adb` via subprocess + `uiautomator2` Python lib | `pip install uiautomator2` (Python-native UIAutomator2 client that wraps the same server); call `adb` binary directly for device management | GADS (AGPL — no code copy), `appium-uiautomator2-driver` (Node.js — reference only) |
| **AWS provisioning** | `boto3` directly + `lyft/awspricing` for pricing | `pip install awspricing` for pricing cache; write preflight and lifecycle against `boto3` EC2/SSM/CloudFormation directly using `cloud-custodian`'s `c7n/resources/ec2.py` as the implementation reference | `cloudformation-cli-python-plugin` (narrow scope, boto3 sufficient) |
| **Runtime agent** | Write from scratch in Python | Thin Python process: SSM-tunneled gRPC or HTTP server on the EC2 instance; receives commands, calls platform observation/action libs, streams back results. No clone — use STF `lib/units/device/` as architecture reference only | Both candidates too divergent to extract from |
| **AX tree extraction** | `viralmind-ai/accessibility-tree-parsers` (desktop) + `uiautomator2` (Android) + Playwright (browser) | Copy `mac-ax/`, `linux-ax/`, `win-ax/` scripts directly into a `devicelab/observation/ax/` module; they are self-contained and output the right JSON schema | `OpenOCR` deferred to Tier 2 — add only when AX proves insufficient; too large to include in MVP |
| **Recipe DSL** | `pypyr/pypyr` | `pip install pypyr` — use as the execution engine; define DeviceLab custom step modules (`pypyr.steps.devicelab.*`) for click, type, observe, assert_screen, capture_artifact | `hyperpotamus` (stale), `testkit` (TypeScript) |
| **Cost guardrails** | `lyft/awspricing` + write cap enforcement ourselves | `pip install awspricing`; write the soft/hard cap state machine in ~200 lines using `cloud-custodian`'s `c7n/actions/core.py` as the pattern reference | `koku` (LGPL + Django — too heavy) |
| **Audit log** | Write from scratch — HMAC-SHA256 chain | ~100 lines of Python: each `AuditEvent` row stores `sha256(prev_hash + payload)`; use `lulzasaur9192/agent-audit-log-examples` `python/` as the seed and expand into the full `AuditEvent` SQLModel entity | `AuditKit` (AGPL), `Trillian` (Go, Merkle overkill for v1) |
| **Secrets** | `jaraco/keyring` | `pip install keyring` — wraps OS keychain on all three platforms; `KeyringBackend` is the IdentityBroker interface; headless Linux fallback via `keyrings.alt` file backend | `infisical` (post-v1 plugin only), `keyring-core` (Rust, use for runtime agent headless Linux if needed) |
| **Network proxy** | `mitmproxy/mitmproxy` | `pip install mitmproxy` — write a single DeviceLab addon class; spawn proxy in-process using `mitmproxy.options.Options` + `DumpMaster`; serialize flows to HAR artifact | `mitmproxy_rs` WireGuard mode deferred to post-v1 when non-browser families need transparent proxying |

---

### Template repo + queue system decision

**Decision: Bring in the template scaffold. Gut the queue. Go straight to MVP code.**

Reasoning:

**Keep the template scaffold** (`MHughesDev/template`) because:
- FastAPI + SQLModel + Postgres + Alembic is exactly the right backend stack for DeviceLab — spending days setting this up from scratch is pure waste
- React 19 + Vite + TanStack is exactly the right frontend — same argument
- Working auth (JWT + argon2), Docker Compose, pytest fixtures, Ruff/mypy, Biome — all done, all correct
- The baseline app is runnable before any DeviceLab code is written — that's the fastest path to an observable system

**Gut the queue** because:
- The current queue has ~80 template-upgrade rows (Q-003, Q-100 through Q-210+) that are about keeping the TEMPLATE repository clean — not building DeviceLab
- Executing those rows would consume weeks of agent time producing documentation cleanup artifacts, not product features
- The queue CSV + QUEUE_INSTRUCTIONS.md governance model adds process overhead that is valuable when you have multiple agents running in parallel but is friction for a focused MVP sprint
- The MVP product rows (Q-101/mvp-1 through Q-116/mvp-6) are the only ones that matter right now

**What to do instead:**
1. Clone the template scaffold into this repo (merge `apps/`, `Makefile`, `compose.yml`, `skills/`, `prompts/`, `scripts/`, etc. from `MHughesDev/template`)
2. Archive ALL template-upgrade queue rows (Q-003, Q-100–Q-138, Q-200–Q-230) — mark done or drop entirely
3. Rewrite the remaining MVP queue rows (Q-101/mvp-1 through Q-116/mvp-6) as a flat sprint backlog in a simpler format — GitHub Issues or a trimmed queue with no governance overhead
4. Start executing Phase 1 (local control plane skeleton) immediately

**The queue system itself** — keep the CSV file as a lightweight backlog tracker but stop treating the QUEUE_INSTRUCTIONS.md governance rules as blocking. For a focused MVP sprint, the right process is: pick the top item, build it, PR it, move on.

---

## Follow-up Tasks

- [x] Per-subsystem comparison table added
- [x] Final decisions locked for all 12 subsystems
- [x] Template vs. direct build decision made
- [ ] Bring template scaffold into this repo
- [ ] Archive all template-upgrade queue rows; keep only mvp-1 through mvp-6 and ops-questions
- [ ] Spike: get the template baseline running locally end-to-end (Docker Compose up, tests green)
- [ ] Begin Phase 1 — Q-101/mvp-1: local control plane skeleton
