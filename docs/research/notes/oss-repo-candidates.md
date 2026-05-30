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

## Follow-up Tasks

- [ ] Per-subsystem comparison table (winner selection per repo candidate)
- [ ] License deep-check on AGPL/LGPL candidates before build dependency decisions
- [ ] Spike PRs for the 3 highest-leverage integrations (MCP SDK, mitmproxy, aiortc)
- [ ] Verify `monoscope-tech/testkit` and `Jreamr/ai-action-ledger` licenses (small repos, spot-check)
