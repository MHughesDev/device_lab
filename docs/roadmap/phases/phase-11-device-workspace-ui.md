---
doc_id: "25.4"
title: "Phase 11 — Device Workspace UI (browser-tab UX)"
section: "Roadmap"
status: "complete"
completion: "100%"
updated: "2026-06-02"
---

# Phase 11 — Device Workspace UI (browser-tab UX)

**Progress: 100%** `██████████` — complete

## Objective

Deliver the **browser-like device workspace**: each device is a named tab; a `+` button opens the
**New / Existing** create wizard; each tab shows a **screen pane** (live when interactive, a headless
placeholder otherwise) over a **backend-process log panel**; and a per-device **options menu**
exposes the full runtime control set. Names are editable and shown on tabs and in the manifest
picker.

---

## What shipped

### Batch A — workspace shell (11-01, 11-02)
- `apps/web/src/stores/deviceTabs.ts` — plain-module tab store, `localStorage` persistence, custom subscriber pattern (no zustand)
- `apps/web/src/hooks/useDeviceTabs.ts` — `useSyncExternalStore` wrapper for React
- `apps/web/src/routes/_layout/workspace.tsx` — tabbed workspace route; tab strip; rename overlay; empty state; session restore on load; active tab wires ScreenPane + LogPanel + ResourceHud + DeviceOptionsMenu
- `apps/web/src/routes/_layout.tsx` updated — workspace gets full-height no-padding layout; other routes keep existing container

### Batch B — create wizard (11-03, 11-04, 11-05)
- `apps/web/src/components/devices/CreateChooser.tsx` — New/Existing chooser dialog
- `apps/web/src/components/devices/NewDeviceWizard.tsx` — 4-step wizard (OS → display-mode → MCP → name); submits `DeviceCreate`; opens new tab
- `apps/web/src/components/devices/ManifestPicker.tsx` — lists manifests from `GET /api/v1/manifests/`; creates-from-manifest on select

### Batch C — per-tab content (11-06, 11-07, 11-08, 11-09, 11-10)
- `apps/web/src/lib/deviceLogs.ts` — SSE client with auto-reconnect
- `apps/web/src/components/devices/LogPanel.tsx` — timestamped log output, level/source filters, autoscroll, download
- `apps/web/src/lib/webrtc/client.ts` — WebRTC negotiation via `POST /stream/negotiate`; video + audio track attach
- `apps/web/src/lib/webrtc/input.ts` — JSON-over-data-channel input serialization (move/mousedown/mouseup/scroll/keydown/keyup/keytext)
- `apps/web/src/lib/webrtc/clipboard.ts` — `ClipboardSync` class; host→device paste intercept; device→host clipboard write
- `apps/web/src/components/devices/ScreenPane.tsx` — WebRTC `<video>` + `<audio>`, headless placeholder + Attach affordance, latency HUD, mute/detach controls; pointer-lock-ready
- `apps/web/src/components/devices/FileDrop.tsx` — drag-and-drop overlay → `POST /devices/{id}/files/push`; progress toast

### Batch C extra (11-11)
- `apps/web/src/lib/webrtc/webcodecsCanvas.ts` — `WebCodecsCanvas`; `VideoDecoder` decode to `<canvas>`; off-by-default power-user path

### Batch D — options menu (11-12, 11-13)
- `apps/web/src/components/devices/DeviceOptionsMenu.tsx` — full action set a–q; terminate confirm; capture manifest; duplicate; pin/unpin
- Rename: inline tab double-click + menu → `PATCH /api/v1/devices/{id}`

### Batch E — polish (11-14, 11-15)
- `apps/web/src/components/devices/ResourceHud.tsx` — RAM/CPU bars vs host total; device count vs max
- `apps/web/src/lib/types.ts` — shared `Device`, `DeviceManifest`, `Template`, `HostResources`, `deviceTitle()` helpers
- Backend: `PATCH /api/v1/devices/{id}` (name/display_mode/mcp_exposed)
- Backend: `POST /api/v1/devices/{id}/files/push` (multipart); `GET /api/v1/devices/{id}/files/pull`
- Backend: `GET /api/v1/host/resources` via new `apps/api/app/api/routes/host.py`
- `apps/api/app/stream/clipboard.py` — family-aware clipboard inject/poll (Linux: xclip; Windows: Set-Clipboard; macOS: pbcopy; Android: am broadcast)
- `apps/web/src/components/Sidebar/AppSidebar.tsx` — Workspace nav item added
- `apps/web/src/routes/_layout/devices.tsx` — "Open" button → `DeviceTabStore.openTab()` + navigate to /workspace
- `apps/web/src/routeTree.gen.ts` — updated to include workspace/devices/onboarding routes
- Vitest config + unit tests (`src/tests/deviceTabs.test.ts`): 14 tests covering open/activate/close/hydrate/pin/terminate-safety
- Playwright E2E test (`tests/e2e/workspace.spec.ts`): 5 smoke scenarios with API mocks

---

## Exit criteria — status

| Criterion | Status |
|-----------|--------|
| Browser-like tab strip; `+` opens New/Existing wizard | ✅ |
| New wizard: OS · location · display-mode · MCP · name | ✅ |
| Existing wizard: manifest picker → create-from-manifest | ✅ |
| Screen pane: live WebRTC video+audio+input when interactive | ✅ |
| Headless placeholder + Attach affordance | ✅ |
| Backend-process log panel (SSE, filters, autoscroll, download) | ✅ |
| All interaction modes: mouse, keyboard, scroll, clipboard, file push/pull | ✅ |
| Options menu a–q; unavailable items disabled-with-tooltip | ✅ |
| Rename: inline tab double-click + menu | ✅ |
| Closing a tab never terminates the device | ✅ |
| Tabs restore on reload; terminated devices dropped | ✅ |
| Resource HUD: RAM/CPU vs host total | ✅ |
| `PATCH /devices/{id}` for rename | ✅ |
| `GET /host/resources` | ✅ |
| File push/pull routes | ✅ |
| E2E smoke test | ✅ |
