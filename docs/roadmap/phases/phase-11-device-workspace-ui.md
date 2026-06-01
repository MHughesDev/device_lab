---
doc_id: "25.4"
title: "Phase 11 — Device Workspace UI (browser-tab UX)"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-06-01"
---

# Phase 11 — Device Workspace UI (browser-tab UX)

**Progress: 0%** `░░░░░░░░░░` — planned

## Objective

Deliver the **browser-like device workspace**: each device is a named tab; a `+` button opens the
**New / Existing** create wizard; each tab shows a **screen pane** (live when interactive, a headless
placeholder otherwise) over a **backend-process log panel**; and a per-device **options menu**
exposes the full runtime control set. Names are editable and shown on tabs and in the snapshot
picker. This is the human face of Phases 08–10.

Read first: `interactive-workspace-plan.md` (all decisions). Stack: React 19 + Vite + TanStack
Router/Query; shadcn-style primitives already exist (`tabs`, `dialog`, `dropdown-menu`, `select`,
`card`, `badge`, `separator`, `sheet`).

---

## Dependency note

- **Log panel, create wizard, options-menu shell, naming** depend only on **Phase 08** (device fields
  + log-stream route) → can start immediately, in parallel with Phase 09.
- **Live screen pane** (WebRTC client) gates on **Phase 09** (attach/detach + real stream).
- **Snapshot picker / Create-from-snapshot** gates on **Phase 10** (snapshot library + create path).

---

## Task batches and dependencies

```
Batch A (workspace shell — depends on Phase 08 model)
  11-01  Tabbed workspace route + tab state store (open/close/reorder/active)
  11-02  Tab session restore (reopen previously-open device tabs on reload)

Batch B (create wizard — depends on Phase 08; Existing branch depends on Phase 10)
  11-03  "+" → New/Existing chooser dialog
  11-04  New flow: OS · location · display-mode · MCP-exposure · name
  11-05  Existing flow: snapshot picker (named list) → create-from-snapshot

Batch C (per-tab content — log panel: Phase 08; screen pane: Phase 09)
  11-06  Backend-process log panel (WS/SSE feed, level/source filters, autoscroll)
  11-07  Screen pane: WebRTC client + input forwarding (interactive)
  11-08  Headless placeholder + "Attach interactive session" affordance
  11-09  Screen pane: optional WebCodecs low-latency canvas path (local power-user)

Batch D (per-device options menu — toggles depend on 08/09/10 as noted)
  11-10  Options menu shell + the full recommended action set (see below)
  11-11  Rename (inline tab edit + menu) wired to PATCH device.name

Batch E (polish)
  11-12  Resource/ledger HUD (per-device RAM/CPU + host budget bar)
  11-13  E2E smoke: open → create new → attach → see frames → logs → snapshot → close
```

---

## Recommended per-device options menu (the full set)

The brief specified (a) MCP on/off and (b) "turn into a stateful machine." Recommended complete set
(D-1 vocabulary; each maps to an existing or planned endpoint):

| # | Action | Maps to | Phase |
|---|--------|---------|-------|
| a | **MCP server on / off** + copy connection details + role scope (Observe/Test/Operate/Admin) | `mcp_exposed` toggle; per-device manifest | 08/03 |
| b | **Attach / Detach interactive session** (the "stateful" toggle → live display) | `display/attach`·`detach` | 09-14 |
| c | **Rename** | `PATCH device.name` | 11-11 |
| d | **Save as snapshot** (named) | `create_snapshot` | 10 |
| e | **Sleep / Wake** (frees / re-reserves host RAM) | `device/sleep`·`wake` | 10 |
| f | **Restart / Reboot** | lifecycle | existing |
| g | **Stop / Terminate** | lifecycle | existing |
| h | **Start / Stop screen recording** (artifact) | recording tools | existing |
| i | **Display & quality** (resolution, fps, sharp-text ⇄ smooth) | stream profiles | 09-15 |
| j | **Open logs full-screen / Download logs** | log bus | 08 |
| k | **Clipboard sync + file push/pull** | channel push/pull | existing |
| l | **Resource usage** (live RAM/CPU/disk) | ledger HUD | 11-12 |
| m | **Network: proxy / mitmproxy** (gated on OQ-012) | local proxy | deferred |
| n | **Duplicate device** (clone from same template/snapshot) | create | 10/existing |
| o | **Pin / reorder tab** | tab store | 11-01 |

Items b, e, i, m are disabled-with-tooltip until their backing phase ships, so the menu is complete
from day one and lights up incrementally.

---

## Task 11-01: Tabbed workspace route + tab store

**Files:** `apps/web/src/routes/_layout/workspace.tsx` (new, becomes the default device view);
`apps/web/src/stores/deviceTabs.ts` (new); reuse `components/ui/tabs.tsx`.

Browser-like tab strip: each open device is a tab titled by `device.title` (name or `family · id8`),
with a close (×) and the `+` button at the right (per the screenshot). Tab store tracks
open/active/order; closing a tab does **not** terminate the device (that's an explicit menu action) —
it just closes the view. Make `/devices` (the old list) the "all devices / reopen" index.

**Tests (Vitest):** `tabStore opens/activates/closes`, `closing tab does not call terminate`,
`tab title falls back to family·id8`.

**Do not:** terminate devices on tab close; conflate view lifecycle with device lifecycle.

---

## Task 11-02: Tab session restore

**Files:** `apps/web/src/stores/deviceTabs.ts` (persist), `workspace.tsx`.

Persist open-tab ids + active tab to `localStorage`; on reload, reopen tabs for devices still alive
(skip terminated). Mirrors a browser restoring its tabs.

**Tests:** `restores live tabs on reload`, `drops terminated devices from restore`.

---

## Task 11-03: New/Existing chooser

**Files:** `apps/web/src/components/devices/CreateChooser.tsx` (new); reuse `dialog`.

`+` opens a dialog: **New** vs **Existing**. Existing → snapshot picker (11-05); New → wizard
(11-04). Back/cancel supported. Matches the brief's two-step gate.

**Tests:** `chooser routes New→wizard and Existing→picker`, `back returns to chooser`.

---

## Task 11-04: New-device wizard

**Files:** `apps/web/src/components/devices/NewDeviceWizard.tsx` (new); reuse `select`, `form`.

Collect (D-1 vocabulary): **Operating System** (family/template, filtered by host capability via the
Phase 07 manifest), **Local or Cloud**, **Display mode** — *Headless (agent-only)* vs *Interactive
(live view)* (rename of "headless/stateful" with helper text explaining MCP still works headless,
D-2), **MCP exposed** yes/no, and optional **Name**. Submits `DeviceCreate`; opens the new device as
a tab.

**Tests:** `wizard collects four axes + name`, `display-mode help explains headless≠no-MCP`,
`submit opens device tab`.

**Do not:** offer families the host can't run locally (respect placement/manifest filtering).

---

## Task 11-05: Existing-snapshot picker

**Files:** `apps/web/src/components/devices/SnapshotPicker.tsx` (new). **Depends on Phase 10.**

List named snapshots (`GET /snapshots?location=local`) with family/OS/size/created; pick → confirm →
`DeviceCreate{snapshot_id}` → auto-open as a tab (the brief's "auto load that one in the web-page
view tab"). Back returns to the chooser.

**Tests:** `picker lists named snapshots`, `selecting creates-from-snapshot and opens tab`,
`back returns to chooser`.

---

## Task 11-06: Backend-process log panel

**Files:** `apps/web/src/components/devices/LogPanel.tsx` (new);
`apps/web/src/lib/deviceLogs.ts` (WS/SSE client). **Depends on Phase 08 (08-12).**

Docked beneath the screen pane: subscribe to `/devices/{id}/logs/stream`, render timestamped,
color-by-`level`, filter by `source` (lifecycle/provisioner/transport/stream/mcp/recording/snapshot/
ledger), autoscroll with pause-on-scroll, search, and a download button. This is the always-present
half of a tab (works for headless devices too).

**Tests:** `log panel renders streamed events`, `filters by source`, `autoscroll pauses on manual scroll`.

**Do not:** render raw secret-bearing fields (server already redacts — UI shows redaction markers).

---

## Task 11-07: Screen pane — WebRTC client

**Files:** `apps/web/src/components/devices/ScreenPane.tsx` (new);
`apps/web/src/lib/webrtc/{client.ts,input.ts}` (new). **Depends on Phase 09.**

Negotiate via the existing `/stream/negotiate`; render the media track into `<video>` with
`playoutDelayHint≈0` for local. Capture keyboard/mouse/scroll → binary input protocol over the data
channel (pointer-move unreliable/coalesced; keys/clicks reliable). Handle reconnect via session
token. Show connection/latency status.

**Tests:** `client negotiates and attaches stream` (mock RTCPeerConnection),
`input events serialize to binary protocol`, `pointer moves coalesced`.

**Do not:** poll screenshots for the live view (that's the MCP path, not the human view, D-2).

---

## Task 11-08: Headless placeholder + Attach affordance

**Files:** `ScreenPane.tsx` (extend).

When `display_mode=headless`, show a clear placeholder ("Headless — agent-operable. Click **Attach
interactive session** to view/control") with the attach button → `display/attach` (09-14), which
flips the tab to the live pane without reprovision. Detach returns to the placeholder.

**Tests:** `headless shows placeholder + attach`, `attach switches to live pane`.

---

## Task 11-09: Optional WebCodecs canvas path

**Files:** `apps/web/src/lib/webrtc/webcodecsCanvas.ts` (new); opt-in toggle in Display & quality.

For local power users: decode raw H.264 AUs over a data channel with **WebCodecs** → `<canvas>`,
bypassing the RTP jitter buffer for the lowest achievable latency (the scrcpy-web pattern). Default
remains the WebRTC `<video>` path; this is an advanced toggle.

**Tests:** `webcodecs path decodes AUs to canvas` (mock VideoDecoder), `falls back to video on unsupported`.

**Do not:** make WebCodecs the default (one supported path; this is additive).

---

## Task 11-10: Options menu shell + action set

**Files:** `apps/web/src/components/devices/DeviceOptionsMenu.tsx` (new); reuse `dropdown-menu`.

Implement the full recommended action set table above. Each item calls its endpoint and reflects
state (e.g., MCP on/off shows current; Attach/Detach reflects display_mode). Actions whose phase
hasn't shipped are disabled with an explanatory tooltip. Destructive actions (Terminate, Delete
snapshot) confirm first.

**Tests:** `menu renders full action set`, `unavailable actions disabled with tooltip`,
`terminate confirms before firing`.

---

## Task 11-11: Rename

**Files:** `workspace.tsx` (inline tab edit), `DeviceOptionsMenu.tsx`; backend `PATCH
/devices/{id}` accepts `name` (add if absent).

Double-click tab title or menu → Rename → `PATCH device.name`; tab + any list update live (D-6).

**Tests:** `rename updates tab title`, `rename persists via PATCH`.

---

## Task 11-12: Resource/ledger HUD

**Files:** `apps/web/src/components/devices/ResourceHud.tsx` (new); `GET /host/resources` (add).

Per-device RAM/CPU and a host-budget bar (committed vs total vs headroom) so the user sees why a
create/wake was refused (D-3). Surfaces sleeping devices' reclaimed RAM.

**Tests:** `hud shows host committed vs total`, `reflects insufficient-resources state`.

---

## Task 11-13: E2E smoke

**Files:** `apps/web/tests/e2e/workspace.spec.ts` (new, Playwright or the project's E2E harness).

Open workspace → `+` → New (headless local Linux) → tab opens → log panel streams → Attach → frames
render → Save as snapshot → close tab (device survives) → reopen from index. Mock the device backend
where needed.

**Do not:** require real GPU/streaming in CI; gate the frame-render assertion behind a capability flag.

---

## Exit criteria

- A user opens device **tabs** like browser pages; `+` runs the **New/Existing** wizard exactly as
  specified (New → OS/location/display-mode/MCP; Existing → named snapshot → auto-opens).
- Each tab shows a **screen pane** (live when interactive, headless placeholder with **Attach**
  otherwise) over a **backend-process log panel**.
- The per-device **options menu** exposes the full recommended set; unavailable actions are clearly
  disabled.
- Devices and snapshots are **renamable**; names are the tab titles and picker labels.
- Closing a tab never terminates a device; tabs restore on reload.
