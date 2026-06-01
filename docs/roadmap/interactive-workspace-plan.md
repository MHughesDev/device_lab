---
doc_id: "25.0"
title: "Interactive Device Workspace — long-term plan"
section: "Roadmap"
status: "current"
completion: "0%"
updated: "2026-06-01"
---

# Interactive Device Workspace — Long-term Plan (Phases 08–12)

**Progress: 20%** `██░░░░░░░░` — 1 of 5 phases complete (08–12); Phase 09 next. Phases 01–07 (local
hosting) already landed; this initiative builds the human-facing, low-latency interactive layer
on top of the local-first runtime.

## Strategic outcome

Turn DeviceLab from an *agent-and-list* tool into an **interactive device workspace** that
feels like a web browser: a user opens, names, and closes device "tabs," each tab showing
a live (or deliberately headless) screen with a backend-process log panel beneath it. Every
device remains fully agent-operable over MCP whether or not a human is watching. Streaming is
**low-latency and hardware-accelerated**, environment manifests make devices reproducible, and the
host's memory is **accounted for and never over-committed**.

This plan assumes and extends the design in `docs/design/streaming-dream-build.md` (the media
layer) and the local-hosting seams from ADR-0003 / Phase 07.

---

## Decisions & reframes (read before implementing)

The user's intent was captured faithfully, with the following **deliberate clarifications**.
Implementing agents must use the reframed vocabulary — it is the source of truth.

### D-1. "Headless vs stateful" is two axes, not one

The original brief offered a single create-time choice: *"headless or stateful machine?"* and a
runtime toggle to *"turn it into a stateful machine."* These conflate two orthogonal concerns.
We split them:

| Axis | Values | Set when | Toggleable at runtime? | Maps to user's words |
|------|--------|----------|------------------------|----------------------|
| **Display mode** | `headless` \| `interactive` | create | **Yes** | "headless" / "stateful machine" / "interactive display" |
| **Manifest-backed** | `yes` \| `no` | create | No (manifest captured via action) | "new" / "existing device" |
| **MCP exposure** | `on` \| `off` | create | **Yes** | "MCP exposed yes or no" |
| **Location** | `local` \| `cloud` | create | No | "local or cloud" |

- **Display mode = headless** → a virtual framebuffer exists on the device, but **no WebRTC
  stream is started**. MCP screenshot / record / AX-tree all work (they read the framebuffer
  directly — see D-2). The tab shows logs only; the screen pane reads "Headless — click *Attach
  interactive session* to view and control."
- **Display mode = interactive** → WebRTC stream + audio track + full input control are live;
  the human drives it. When interactive, the device **always** has screen, audio, mouse,
  keyboard, clipboard, and file push/pull — there is no interaction-less interactive mode.
- The runtime menu item the user called *"turn into a stateful machine"* is renamed
  **"Attach interactive session"** (and its inverse, **"Detach"**). It flips display mode
  `headless → interactive` with no reprovision.
- **"Existing / snapshot devices"** are manifest-backed: they are created via **Create-from-manifest**
  (Phase 10). There is **no sleep/wake state** — a device is either running or terminated.
  "Sleepy machine" (user's term) simply means a running device that isn't under load — it remains
  fully allocated and is not a special state.

### D-2. The MCP screen and the human screen are independent consumers

Confirmed earlier in conversation and load-bearing for the whole UI: the MCP `screenshot`/
`recording`/`ax_tree` tools read the device framebuffer **directly via OS-native capture**
(`adb screencap`, `scrot`, ScreenCaptureKit, `simctl io`). They do **not** depend on a running
WebRTC stream and do **not** require the web app to display anything. "Headless" therefore means
*"not streamed to a human,"* not *"no framebuffer."* The currently-broken `-display none` /
no-Xvfb states (which destroy the framebuffer itself) are bugs fixed in Phase 08, not a "headless"
mode.

### D-3. Memory must be a first-class, consolidated ledger — never over-committed

The brief: *"clear memory allocation for each device … nothing overlapping … memory always
[reserved] and consolidated."* Phase 07 already ships `LocalScheduler` admission control
(`services/local/scheduler.py`). We **extend** it into a durable **Host Resource Ledger** (Phase 08):

- Every device template declares a RAM/vCPU/disk reservation.
- The ledger tracks **committed vs total** across all running local devices and refuses any
  create that would over-commit (→ `preflight_blocked: insufficient_host_resources`).
- A device holds its full reservation from `provisioning` until `terminated` — there is no
  intermediate "sleeping" state that reclaims RAM.
- Reservations are persisted so a control-plane restart reconciles the ledger against reality
  (extends Phase 07's startup reconciliation).

### D-4. "Backend process logs" — defined

The per-tab log panel (delegated to our discretion) is a **structured, timestamped, secret-redacted
per-device event stream** (`DeviceLogEvent`) multiplexing:

1. FSM/lifecycle transitions (`requested → provisioning → ready …`).
2. Provisioner subprocess output (qemu / emulator / docker / avdmanager / vz), line-tagged.
3. Transport/channel command activity (adb / ssh / docker-exec / ssm) — **secrets redacted**.
4. Stream-session events (negotiate, ICE state, keyframe, bitrate change, reconnect, teardown).
5. MCP tool invocations against this device (tool, role, allow/deny decision) — links to Evidence.
6. Recording & manifest-capture events; resource-ledger events (reserved / released N MB).
7. Warnings & errors.

Delivered to the UI over a per-device **WebSocket/SSE** feed backed by a bounded ring buffer
(persist last N to DB for post-mortem). Never put plaintext secrets in the stream (honors the
no-plaintext-secrets invariant).

### D-5. Streaming media-path decisions (locked by user)

- **(A)** aiortc with an **encoded-passthrough track** — keep the locked WebRTC dep; no GStreamer
  `webrtcbin`.
- **macOS local** → **Virtualization.framework (`vz`)** on Apple Silicon (drop QEMU there);
  capture via **ScreenCaptureKit**, encode via **VideoToolbox**.
- **QEMU capture** → start with a **VNC-bridge** (works everywhere); upgrade to
  **virtio-gpu-gl + egl-headless/D-Bus + VA-API/NVENC** where a host GPU exists.

### D-6. Naming

Devices **and** manifests get an optional user-supplied `name` (≤120 chars). It is the tab title
and the label in the manifest/existing-device picker. Absent a name, fall back to
`<family> · <id8>`. New `name` columns on `Device` and `DeviceManifest` (Alembic migrations).

---

### D-7. Manifests capture the recipe, not the data (decided 2026-06-01)

A `DeviceManifest` records installed software, env, and config — **not** in-application data,
on-device databases, user files, or session state (`docker build`, not `docker commit`). This
keeps manifests portable, inspectable, and cross-family. We deliberately **do not** build a
local-first / cross-family data-capture mechanism. The only byte-for-byte data capture is the
existing **Phase 05 EBS snapshot (cloud Linux only)**. Users needing stateful data either bake
seed data into `install_steps`, externalize it themselves, or use an EBS snapshot where supported.
Devices from manifests are cattle, not pets. See Phase 10 "Non-goal" section for full consequences.

---

## Conceptual model (the four axes, one diagram)

```
Create a device
   ├── New ──────────────► choose: OS · location · display-mode · MCP-exposure  (+ optional name)
   │                          └─► provisions a fresh base image
   └── Existing ─────────► pick a named DeviceManifest ──► Create-from-manifest
                               (provisions fresh base + installs everything from the spec)

Runtime (per tab)
   display_mode:  headless  ⇄  interactive     ("Attach / Detach interactive session")
                                               interactive = screen + audio + ALL input (no partial)
   mcp_exposed:   on        ⇄  off
   power:         running (resources committed)  →  terminated (resources released)
                  no intermediate sleep/suspend state

Capture (from running device)
   "Capture environment manifest" ──► DeviceManifest saved to registry (named, reusable)
```

---

## Phase map (this initiative)

| Phase | Theme | Key deliverable |
|-------|-------|-----------------|
| **08** | Display & Resource Foundations | Real framebuffers for every family; the 4-axis device model (`name`, `display_mode`, `mcp_exposed`); Host Resource Ledger (no over-commit, no suspended state); per-device structured log bus |
| **09** | Low-Latency Streaming Media Layer | `MediaSource`/`InputSink` SPI; aiortc encoded-passthrough; per-family hardware capture+encode (Android scrcpy first); video+audio+input; attach/detach; quality profiles; local-vs-cloud ICE |
| **10** | Device Manifests & Environment Registry | Declarative `DeviceManifest` (named environment spec, not a disk image); manifest registry; capture-from-device; create-from-manifest; import/export |
| **11** | Device Workspace UI (browser-tab UX) | Tabbed workspace shell; New/Existing create wizard; per-tab screen pane + log panel; full per-device options menu; naming UI; manifest picker; tab session restore |
| **12** | Root & Cloud Infra Settings | Server-level settings: cloud infra (AWS via SecretRef), local host budget, streaming, MCP, manifests, security — wired and validated |

### Dependency graph

```
08 ──► 09 ──► 11 (screen pane)
  └──► 10 ──► 11 (manifest picker, create-from-manifest)
08 ──────────► 11 (log panel, create wizard, options shell can start early)
08 ──► 12 (host budget settings)  ;  09 ──► 12 (streaming settings)  ;  10 ──► 12 (manifest settings)
```

Phase 11's **log panel, create wizard, and options-menu shell** depend only on Phase 08, so the
frontend can begin in parallel with Phase 09/10; the **live screen pane** gates on Phase 09 and the
**manifest picker** on Phase 10.

---

## OSS / dependencies introduced (each needs an ADR before its phase ships)

| Subsystem | Package / source | Phase | Notes |
|-----------|-----------------|-------|-------|
| Desktop capture+encode pipeline | **GStreamer** (+ `python-gst` bindings) | 09 | one pipeline framework; swap `src`/`enc` per family/location |
| Android mirror+control | **scrcpy-server** jar + `adb` | 09 | device-native MediaCodec H.264; finishes the existing Android stream stub |
| macOS local VM | **Virtualization.framework** (`vz`, via PyObjC or a small Swift helper) | 09/10 | replaces QEMU on Apple Silicon |
| macOS/iOS capture + encode | **ScreenCaptureKit** + **VideoToolbox** | 09 | replaces `screencapture`/`simctl io` for the *live* path |
| Linux virtual display | **Xvfb** (baseline) / virtio-GPU + VA-API (GPU hosts) | 08/09 | fixes the no-framebuffer bug |
| Cloud NAT traversal | **coturn** (user VPC) | 09 (cloud subtasks) | research note already calls for it; **cloud only** |
| Encoded-frame passthrough | thin **aiortc** extension (~120 LOC) | 09 | keeps locked dep; no second WebRTC stack |
| Per-device log transport | FastAPI **WebSocket/SSE** (stdlib + starlette) | 08 | no new dep |

Locked deps (`aiortc`, `mcp`/FastMCP, `uiautomator2`, `boto3`/`awspricing`, `pypyr`, `keyring`,
`mitmproxy`) are **not** swapped. GStreamer/scrcpy/`vz`/coturn are **additive** and each gets a
one-page ADR per the `oss-repo-candidates.md` discipline.

---

## Cross-cutting invariants (unchanged, must be honored)

- **Localhost-only control plane** — the device WS/SSE log feeds and the local WebRTC signaling bind
  to loopback only; local ICE uses a single `127.0.0.1` host candidate (no STUN/TURN locally).
- **No plaintext secrets in model context** — cloud creds via `keyring`/SecretRef (Phase 12); log
  bus redacts secrets (D-4).
- **Append-only audit log** — MCP-toggle, attach-session, manifest-capture, terminate, and settings
  changes emit audit events; never mutate existing entries.
- **BYOC hard boundary** — cloud streaming encodes on the user's EC2; coturn deploys into the user's
  VPC; DeviceLab hosts nothing.
- **Adapter SPI** — `MediaSource`/`InputSink`/manifest-capture ops are per-family plugins behind the
  SPI; no family-specific logic in core.

---

## Phase exit gates (apply to every phase in this initiative)

A phase is complete when:
- Its happy path runs end-to-end and is documented.
- Every new service contract has success + failure tests.
- Every dangerous/expensive/secret path passes a policy check and emits an audit event.
- New deps have a merged ADR.
- Round-trip / latency budgets (Phase 09) have automated acceptance tests.

---

## Latency & quality acceptance budgets (Phase 09 gates)

| Path | Glass-to-glass | Input-to-photon |
|------|----------------|-----------------|
| Local, hardware encode | < 50 ms (stretch 30 ms) | < 40 ms |
| Local, software x264 | < 100 ms | < 80 ms |
| Cloud, same region | < 150 ms | < 120 ms |

---

## Risks

| Risk | Mitigation |
|------|------------|
| aiortc encoded-passthrough proves brittle across families | Spike it first (task 09-02) on Android before per-family work; ADR records fallback to GStreamer `webrtcbin` if it fails |
| `vz` requires native (Swift/PyObjC) glue that complicates the Python control plane | Isolate behind a small sidecar helper with a typed RPC; keep the Python SPI clean |
| Memory ledger drift after crashes leaks reservations | Persist reservations; reconcile against `psutil`/hypervisor reality on startup (extends Phase 07) |
| Tabbed UI tempts us to gold-plate before streaming works | UI log panel + wizard ship on Phase 08; the live pane is explicitly gated on Phase 09 acceptance budgets |
| Users assume a manifest restores their data (DB rows, files) and lose state | Manifests are recipe-only by decision (D-7); UI labels "Capture environment manifest" as environment-not-data; docs point to Phase 05 EBS snapshot as the only byte-for-byte path (cloud Linux) |
