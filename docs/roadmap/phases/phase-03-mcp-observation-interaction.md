---
doc_id: "24.4"
title: "Phase 03 — MCP observation and interaction"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-05-31"
---

# Phase 03 — MCP Observation and Interaction

**Progress: 0%** `░░░░░░░░░░` — not started

## Objective

Make DeviceLab genuinely useful to AI agents without relying on screenshot loops. Agents should discover only the tools valid for the selected device family and state, observe structured AX/OCR state first, execute semantic actions, and batch steps with optimistic screen-version guards. Every action produces a typed evidence envelope.

---

## OSS pulled in this phase

| Repo / package | What we take | Where it lands |
|----------------|-------------|----------------|
| `mcp` / FastMCP | Tool groups, capability handshake, filtered manifests, MCP elicitation hooks | `apps/api/app/mcp/` |
| `viralmind-ai/accessibility-tree-parsers` | Copy 3 scripts verbatim (MIT): `linux_ax.py`, `macos_ax.py`, `windows_ax.py` | `apps/api/app/adapters/ax/` |
| `browser-use` | `browser_use/dom/` — DOM extraction + AX snapshot for browser observation tier | `apps/api/app/adapters/browser/observation.py` |
| `uiautomator2` (`pip install uiautomator2`) | Android AX tree dump and element interaction (phase 03 Android stub; full in phase 06) | `apps/api/app/adapters/android/observation.py` |
| `appium/appium-uiautomator2-driver` (reference) | `lib/commands/` — reference for every Android action shape DeviceLab needs to implement | Patterns ported into Android adapter |

---

## Implementation tasks

### 1. Capability schema

Files: `apps/api/app/mcp/capabilities.py`

Define typed capability declarations that drive tool manifest generation and template catalog:

```python
class DeviceCapabilities(BaseModel):
    lifecycle: LifecycleCapabilities    # provision, stop, start, terminate, snapshot
    observe: ObserveCapabilities        # ax_tree, ocr, screenshot, vlm
    interact: InteractCapabilities      # click, type, fill_form, select, scroll, key
    read_content: ReadCapabilities      # text, headings, tables, links, regions
    files: FileCapabilities             # upload, download, path_read
    network: NetworkCapabilities        # proxy, capture, inject
    recipes: bool
    streaming: bool
    dangerous_mode: bool
```

Each capability field is `true/false` or a typed sub-object. Adapters declare their capabilities at registration time. MCP manifests are generated from the intersection of (device capability) ∩ (MCP client permission role).

### 2. MCP permission roles

Files: `apps/api/app/mcp/permissions.py`

Six roles, each a superset of the previous:

```
Observe     → list_devices, workspace_status, observe
Interact    → + interact, read_content
Test        → + files, recipes (read-only)
Manage      → + recipes (write), templates, lifecycle
Admin       → + cloud_accounts, bootstrap, cost_policy
Dangerous   → + force_terminate, snapshot_delete, raw_shell
```

Role is declared in the MCP client registration and stored per-client. Tool manifest generation filters to only tools the role permits.

### 3. Capability handshake + filtered manifest

Files: `apps/api/app/mcp/gateway.py`, `apps/api/app/mcp/manifest.py`

When an MCP client connects to a specific device:

```
POST /mcp/sessions
  body: { device_id, client_id, requested_role }
  → { session_id, protocol_version, tool_groups, limits, warnings }
```

`tool_groups` is the filtered tool manifest — only tools valid for:
- This device family (browser vs linux vs android)
- This device state (cannot interact with a stopped device)
- This client's permission role

FastMCP supports dynamic tool registration; use `mcp.remove_tool()` and `mcp.add_tool()` per session or use a routing layer that checks session context on every call.

### 4. Observation hub

Files: `apps/api/app/services/observation.py`, `apps/api/app/mcp/tools/observe.py`

Observation tiers (tried in order, escalating only on failure or explicit request):

```
Tier 1: AX tree    → fastest, most structured, preferred
Tier 2: OCR index  → fallback when AX not available or sparse
Tier 3: Screenshot → metadata + image, returned as artifact ref
Tier 4: VLM        → only when dangerous_mode + explicit tier=vlm param
```

Observation envelope:

```python
class ObservationEnvelope(BaseModel):
    device_id: str
    screen_version: int          # monotonic, increments on every state change
    tier: Literal["ax", "ocr", "screenshot", "vlm"]
    structured: dict | None      # AX tree or OCR index
    screenshot_ref: str | None   # artifact id
    delta_from_version: int | None
    warnings: list[str]
    observed_at: datetime
```

**Linux AX**: use `linux_ax.py` copied from `viralmind-ai/accessibility-tree-parsers` — this script extracts the AT-SPI accessibility tree via D-Bus and returns a JSON structure.

**Browser AX**: port `browser_use/dom/buildDomTree.js` and `browser_use/dom/` Python extraction into `apps/api/app/adapters/browser/observation.py`. `browser-use`'s DOM extractor is the best open-source implementation of AX snapshot from a live Playwright page.

**macOS AX**: use `macos_ax.py` copied from `viralmind-ai` — AppleScript/AXUIElement-based tree.

**Windows AX**: use `windows_ax.py` from `viralmind-ai` — UIA-based tree via `pywinauto` under the hood.

### 5. Screen versioning

Files: `apps/api/app/services/screen_version.py`

Every observation increments a `screen_version` counter stored per device in Redis or in a fast DB table. Rules:
- Counter increments on: any action completion, any content-changing observation, device state transition.
- Counter never decrements.
- Observation responses always include current `screen_version`.
- Action requests may include `expected_screen_version`; mismatch → `SCREEN_VERSION_CONFLICT` error.

Delta computation: store the last N observation snapshots per device. Delta endpoint returns structural diff between two versions (added/removed/modified nodes).

### 6. Semantic interaction tools

Files: `apps/api/app/mcp/tools/interact.py`, `apps/api/app/services/interaction.py`

MCP tools:

```python
@mcp.tool()
def click(device_id: str, target: str, expected_screen_version: int | None) -> ActionResult: ...

@mcp.tool()
def type_text(device_id: str, target: str, text: str, ...) -> ActionResult: ...

@mcp.tool()
def fill_form(device_id: str, fields: dict[str, str], ...) -> ActionResult: ...

@mcp.tool()
def select_option(device_id: str, target: str, value: str) -> ActionResult: ...

@mcp.tool()
def scroll(device_id: str, direction: str, amount: int) -> ActionResult: ...

@mcp.tool()
def wait_for(device_id: str, condition: str, timeout_ms: int) -> ActionResult: ...

@mcp.tool()
def read_content(device_id: str, selector: str | None, format: str) -> ContentResult: ...
```

Target resolution order: accessible name → role+text → CSS selector (browser only) → coordinates (fallback, logged as warning).

Action result always contains:
```python
class ActionResult(BaseModel):
    success: bool
    before_screen_version: int
    after_screen_version: int
    observation_delta: dict | None
    evidence_id: str
    warnings: list[str]
    error: str | None
```

Port the action execution patterns from `appium/appium-uiautomator2-driver`'s `lib/commands/` as a reference for Android action shapes — specifically how it handles element resolution, wait conditions, and error classification.

### 7. `run_steps` batching

Files: `apps/api/app/mcp/tools/batch.py`

```python
@mcp.tool()
def run_steps(
    device_id: str,
    steps: list[Step],           # [{action, params, wait_after_ms, expected_screen_version}]
    abort_on_failure: bool = True,
    screen_version_guard: int | None = None,
) -> BatchResult: ...
```

Execution model:
1. Check `screen_version_guard` before starting — abort if mismatch.
2. Execute steps sequentially, each producing an `ActionResult`.
3. On failure: stop immediately if `abort_on_failure`, else continue and mark step as failed.
4. Return all step results, overall `success`, and final `screen_version`.

This is the primary AI agent interaction primitive — batch reduces round trips by 5–10x on typical flows.

### 8. Evidence persistence

Files: `apps/api/app/services/evidence.py`

Every MCP action call (interact, run_steps, observe) creates an `Evidence` record:

```python
class Evidence(SQLModel, table=True):
    id: str                      # uuid
    session_id: str
    device_id: str
    mcp_tool: str
    request_payload: dict        # redacted — no raw secrets
    policy_decision: str         # allow / warn / block
    before_screen_version: int
    after_screen_version: int
    observation_before_ref: str  # artifact id
    observation_after_ref: str   # artifact id
    warnings: list[str]
    created_at: datetime
    audit_event_id: str          # linked AuditEvent
```

Evidence is append-only. Raw secret values are never stored — only SecretRef names.

### 9. MCP tools for device and workspace

Files: `apps/api/app/mcp/tools/inventory.py`

```python
@mcp.tool()
def workspace_status() -> WorkspaceStatus: ...

@mcp.tool()
def list_devices(state: str | None, family: str | None) -> list[DeviceSummary]: ...

@mcp.tool()
def get_device(device_id: str) -> DeviceDetail: ...

@mcp.tool()
def list_templates(family: str | None) -> list[TemplateSummary]: ...

@mcp.tool()
def get_evidence(evidence_id: str) -> Evidence: ...

@mcp.tool()
def cost_status(device_id: str | None) -> CostStatus: ...
```

---

## Error codes (MCP layer)

| Code | Meaning |
|------|---------|
| `DEVICE_NOT_READY` | Tool requires ready session but device is not in ready state |
| `CAPABILITY_UNSUPPORTED` | Device family or state does not support the requested tool |
| `SCREEN_VERSION_CONFLICT` | Expected screen version does not match current |
| `TARGET_NOT_FOUND` | Semantic target cannot be resolved in current AX tree |
| `ACTION_UNSAFE` | Permission check or dangerous-mode gate blocked the action |
| `ACTION_TIMEOUT` | Wait condition exceeded configured budget |
| `OBSERVATION_TIER_UNAVAILABLE` | Requested tier (e.g. VLM) is not enabled |

---

## Exit criteria

- MCP clients connecting to a Linux device receive a manifest with only Linux-valid tools.
- MCP clients connecting to a browser device receive a browser-appropriate manifest.
- Structured AX observation works for Linux and browser without requiring a screenshot.
- `run_steps` batching executes 3+ steps and returns partial results on mid-sequence failure.
- Screen version conflict detection works in unit tests.
- Every `interact` call produces a persisted `Evidence` record with before/after observation refs.
- UI and MCP paths call the same underlying `interaction.py` service — no duplicated logic.
