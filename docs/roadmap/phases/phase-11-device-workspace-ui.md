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
exposes the full runtime control set. Names are editable and shown on tabs and in the manifest
picker. This is the human face of Phases 08–10.

Read first: `interactive-workspace-plan.md` (all decisions). Stack: React 19 + Vite + TanStack
Router/Query; shadcn-style primitives already exist (`tabs`, `dialog`, `dropdown-menu`, `select`,
`card`, `badge`, `separator`, `sheet`).

---

## Dependency note

- **Log panel, create wizard, options-menu shell, naming** depend only on **Phase 08** (device fields
  + log-stream route) → can start immediately, in parallel with Phase 09.
- **Live screen pane** (WebRTC client) gates on **Phase 09** (attach/detach + real stream).
- **Manifest picker / Create-from-manifest** gates on **Phase 10** (manifest registry + create path).

---

## Task batches and dependencies

```
Batch A (workspace shell — depends on Phase 08 model)
  11-01  Tabbed workspace route + tab state store (open/close/reorder/active)
  11-02  Tab session restore (reopen previously-open device tabs on reload)

Batch B (create wizard — depends on Phase 08; Existing branch depends on Phase 10)
  11-03  "+" → New/Existing chooser dialog
  11-04  New flow: OS · location · display-mode · MCP-exposure · name
  11-05  Existing flow: manifest picker (named list) → create-from-manifest

Batch C (per-tab content — log panel: Phase 08; screen pane + audio + full interaction: Phase 09)
  11-06  Backend-process log panel (WS/SSE feed, level/source filters, autoscroll)
  11-07  Screen pane: WebRTC client + video + audio + mouse/keyboard input
  11-08  Clipboard sync (bidirectional host ↔ device)
  11-09  File push / pull via screen pane drag-and-drop
  11-10  Headless placeholder + "Attach interactive session" affordance
  11-11  Screen pane: optional WebCodecs low-latency canvas path (local power-user)

Batch D (per-device options menu — toggles depend on 08/09/10 as noted)
  11-12  Options menu shell + the full recommended action set (see below)
  11-13  Rename (inline tab edit + menu) wired to PATCH device.name

Batch E (polish)
  11-14  Resource/ledger HUD (per-device RAM/CPU + host budget bar)
  11-15  E2E smoke: open → create new → attach → see frames + hear audio → clipboard → file → logs → manifest → close
```

---

## Per-device options menu (the full set)

The brief specified (a) MCP on/off and (b) "turn into a stateful machine." Complete set, with user's
vocabulary aligned to D-1 reframes:

| # | Action | Maps to | Phase |
|---|--------|---------|-------|
| a | **MCP server on / off** + copy connection string + role scope (Observe/Test/Operate/Admin) | `mcp_exposed` toggle; per-device manifest | 08 |
| b | **Attach / Detach interactive session** ("stateful" → live display+audio+input) | `display/attach`·`detach` | 09-14 |
| c | **Rename** | `PATCH device.name` | 11-13 |
| d | **Capture environment manifest** (saves the *environment* — software/config — **not** in-app data or databases; label this clearly) | `capture_manifest` + registry create | 10 |
| e | **Restart / Reboot** | lifecycle | existing |
| f | **Stop / Terminate** | lifecycle | existing |
| g | **Start / Stop screen recording** (artifact to S3 / local) | recording tools | existing |
| h | **Display & quality** (resolution, fps, sharp-text ⇄ smooth) | stream profiles | 09-15 |
| i | **Open logs full-screen / Download logs** | log bus | 08 |
| j | **File push** (drag a local file onto the device) | channel push_file | 11-09 |
| k | **File pull** (download a file from the device) | channel pull_file | 11-09 |
| l | **Clipboard sync** (toggle bidirectional host ↔ device clipboard) | data channel | 11-08 |
| m | **Audio on/off** (mute/unmute device audio in the browser tab) | audio track | 09-16 |
| n | **Resource usage** (live RAM/CPU/disk) | ledger HUD | 11-14 |
| o | **Network: proxy / mitmproxy** (gated on OQ-012) | local proxy | deferred |
| p | **Duplicate device** (provision another from the same manifest/template) | create | 10 |
| q | **Pin / reorder tab** | tab store | 11-01 |

Items b, h, o are disabled-with-tooltip until their backing phase ships. Everything else is available
from day one of Phase 11.

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

`+` opens a dialog: **New** vs **Existing**. Existing → manifest picker (11-05); New → wizard
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

## Task 11-05: Existing-manifest picker

**Files:** `apps/web/src/components/devices/ManifestPicker.tsx` (new). **Depends on Phase 10.**

List named manifests (`GET /api/v1/manifests?location=local`) with family, description, and
created date. Pick → confirm → `DeviceCreate{manifest_id}` → auto-open as a tab. Back returns to
the chooser.

**Tests:** `picker lists named manifests`, `selecting creates-from-manifest and opens tab`,
`back returns to chooser`.

---

## Task 11-06: Backend-process log panel

**Files:** `apps/web/src/components/devices/LogPanel.tsx` (new);
`apps/web/src/lib/deviceLogs.ts` (WS/SSE client). **Depends on Phase 08 (08-12).**

Docked beneath the screen pane: subscribe to `/devices/{id}/logs/stream`, render timestamped,
color-by-`level`, filter by `source` (lifecycle/provisioner/transport/stream/mcp/recording/manifest/
ledger), autoscroll with pause-on-scroll, search, and a download button. This is the always-present
half of a tab (works for headless devices too).

**Tests:** `log panel renders streamed events`, `filters by source`, `autoscroll pauses on manual scroll`.

**Do not:** render raw secret-bearing fields (server already redacts — UI shows redaction markers).

---

## Task 11-07: Screen pane — WebRTC video + audio + input

**Files:** `apps/web/src/components/devices/ScreenPane.tsx` (new);
`apps/web/src/lib/webrtc/{client.ts,input.ts}` (new). **Depends on Phase 09.**

Negotiate via `/stream/negotiate`; render the video track into `<video>` and the audio track into a
hidden `<audio>` element with `playoutDelayHint≈0` for local. Capture **all** interaction modes:

- **Mouse:** pointer-move (unreliable/coalesced), click/scroll (reliable) → binary data channel.
- **Keyboard:** keydown/keyup (reliable channel, preserves modifiers).
- **Scroll:** wheel events → pointer scroll message.
- Pointer lock (click-to-capture) for full-screen control.

Handle reconnect via session token. Show connection, latency, and audio-level status.

**Tests:** `client negotiates video and audio tracks`, `input events serialize to binary protocol`,
`pointer moves coalesced`, `audio element attaches to audio track`.

**Do not:** poll screenshots for the live view (that's the MCP path — D-2). Do not make audio
optional — it is always attached in interactive mode.

---

## Task 11-08: Clipboard sync (bidirectional host ↔ device)

**Files:** `apps/web/src/lib/webrtc/clipboard.ts` (new); backend `stream/clipboard.py` (new);
edit `stream/peer.py` to add a dedicated `"clipboard"` data channel.

A second reliable RTCDataChannel (`"clipboard"`) carries clipboard events in both directions:
- **Host → device:** intercept `paste` events in the pane; send clipboard text over the channel;
  the server injects it via the family's clipboard write mechanism (xclip/xsel on Linux,
  pbcopy on macOS, `adb shell am broadcast ACTION_SEND_TEXT` on Android, PowerShell
  `Set-Clipboard` on Windows).
- **Device → host:** the server polls (or is notified of) clipboard changes on the device and
  pushes updates over the channel; the browser writes to `navigator.clipboard`.
Clipboard sync is user-togglable (off by default — enable in the options menu).

**Tests:** `clipboard channel carries host-to-device paste`, `clipboard channel carries device-to-host copy`,
`clipboard sync disabled by default`.

**Do not:** sync binary clipboard (images, files) in this task — text only.

---

## Task 11-09: File push / pull via the screen pane

**Files:** `apps/web/src/components/devices/FileDrop.tsx` (new); extend `api/routes/devices.py`;
reuse `channel.push_file`/`pull_file`.

**Push:** drag a local file onto the screen pane → `POST /devices/{id}/files/push` (multipart) →
`channel.push_file` to a configurable remote path (default `/tmp/` or `/sdcard/Download/`). Show
progress toast. **Pull:** right-click on the pane or options menu → "Pull file" → prompt for
remote path → `GET /devices/{id}/files/pull?path=…` → `channel.pull_file` → browser download.

**Tests:** `file push multipart → channel push_file`, `file pull → channel pull_file → download`,
`push rejected above size limit`.

**Do not:** implement a remote file browser in this task — manual path entry only.

---

## Task 11-10: Headless placeholder + Attach affordance

**Files:** `ScreenPane.tsx` (extend).

When `display_mode=headless`, show a clear placeholder: *"Headless — fully agent-operable via MCP.
Click **Attach interactive session** to view and control."* The Attach button → `display/attach`
(09-14) flips the tab to the live pane (video + audio + input) without reprovision. Detach returns
to the placeholder.

**Tests:** `headless shows placeholder + attach button`, `attach switches to live pane`,
`detach returns to placeholder`.

---

## Task 11-11: Optional WebCodecs canvas path

**Files:** `apps/web/src/lib/webrtc/webcodecsCanvas.ts` (new); opt-in toggle in Display & quality.

For local power users who want the absolute minimum latency: decode raw H.264 AUs over a data
channel with **WebCodecs** → `<canvas>`, bypassing the RTP jitter buffer entirely (the scrcpy-web
pattern). Default remains WebRTC `<video>`. This is an advanced toggle in the Display & quality
menu; the audio track still uses the WebRTC audio element.

**Tests:** `webcodecs path decodes AUs to canvas` (mock VideoDecoder), `falls back to video on unsupported`.

**Do not:** make WebCodecs the default — `<video>` is the supported path; this is additive.

---

## Task 11-12: Options menu shell + action set

**Files:** `apps/web/src/components/devices/DeviceOptionsMenu.tsx` (new); reuse `dropdown-menu`.

Implement the full action set table above (items a–q). Each item reflects live state (MCP on/off,
display_mode, recording active, audio muted). Items `b`, `h`, `o` are disabled-with-tooltip until
their backing phase ships. Destructive actions (Terminate) confirm first.

**Tests:** `menu renders full action set`, `unavailable actions disabled with tooltip`,
`terminate confirms before firing`, `capture manifest triggers registry create`.

---

## Task 11-13: Rename

**Files:** `workspace.tsx` (inline tab edit), `DeviceOptionsMenu.tsx`; backend `PATCH /devices/{id}`
accepts `name` (add if absent).

Double-click tab title or menu → Rename → `PATCH device.name`; tab + any open list updates live (D-6).

**Tests:** `rename updates tab title`, `rename persists via PATCH`, `manifest rename wired to PATCH /manifests/{id}`.

---

## Task 11-14: Resource/ledger HUD

**Files:** `apps/web/src/components/devices/ResourceHud.tsx` (new); `GET /api/v1/host/resources` (add).

Per-device RAM/CPU/disk indicators and a host-budget bar (committed vs total vs headroom) so the
user sees immediately why a create was refused (`preflight_blocked: insufficient_host_resources`).

**Tests:** `hud shows host committed vs total`, `reflects preflight-blocked reason`.

---

## Task 11-15: E2E smoke

**Files:** `apps/web/tests/e2e/workspace.spec.ts` (new).

Open workspace → `+` → New (headless local Linux, named "Test Env") → tab opens with correct title →
log panel streams lifecycle events → Attach → video + audio render → paste clipboard text → drag-drop
file → Capture manifest → manifest appears in picker → close tab (device survives) → reopen from
index → terminate. Mock GPU/streaming where unavailable in CI.

**Do not:** gate the full smoke on real HW encode — mock the stream and assert UI state only.

---

## Exit criteria

- A user opens device **tabs** exactly like browser pages; `+` opens the **New/Existing** wizard
  (New → OS/location/display-mode/MCP/name; Existing → named manifest → auto-opens as a named tab).
- Each tab shows a **screen pane** (video + audio + all interaction when interactive; headless
  placeholder + Attach affordance otherwise) over a **backend-process log panel**.
- **All interactions** are available in interactive mode: mouse, keyboard, clipboard sync,
  file push/pull via the pane, and audio out. There is no interaction-less interactive screen.
- The per-device **options menu** exposes the full recommended set (a–q); unavailable actions
  are disabled with an explanatory tooltip; no interaction capability is deferred post-Phase 11.
- Devices and manifests carry user-editable **names** that appear as tab titles and picker labels.
- Closing a tab never terminates a device; open tabs restore on reload.
