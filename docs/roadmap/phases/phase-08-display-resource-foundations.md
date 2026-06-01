---
doc_id: "25.1"
title: "Phase 08 — Display & Resource Foundations"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-06-01"
---

# Phase 08 — Display & Resource Foundations

**Progress: 0%** `░░░░░░░░░░` — planned

## Objective

Make every local device family own a **real framebuffer** (fixing the broken `-display none` /
no-Xvfb states), introduce the **four-axis device model** (`name`, `display_mode`, `mcp_exposed`
alongside the existing `location`), build the **Host Resource Ledger** so host RAM is accounted for
and never over-committed, and stand up the **per-device structured log bus** the workspace UI will
consume. This phase ships **no streaming and no UI screen pane** — it makes both possible.

Read first: `docs/roadmap/interactive-workspace-plan.md` (esp. decisions D-1…D-5) and
`docs/roadmap/phases/phase-07-local-hosting.md`.

---

## OSS pulled in this phase

| Package / source | What we take | Where it lands |
|------------------|--------------|----------------|
| `Xvfb` (system pkg, documented not vendored) | Virtual X framebuffer inside Linux containers | `adapters/linux/local_provision.py`, container entrypoint |
| QEMU `virtio-vga` / `virtio-gpu` (already have QEMU) | Real display adapter for Windows/macOS VMs | `adapters/windows/local_provision.py`, `adapters/macos/local_provision.py` |
| FastAPI WebSocket/SSE (starlette, already in) | Per-device log feed | `api/routes/device_logs.py`, `services/device_log_bus.py` |

No new pip dependencies (Xvfb/QEMU are system deps documented in host-prerequisites). The
`vz`/ScreenCaptureKit work is Phase 09; here macOS only gains a display adapter under QEMU as a
stop-gap, gated on Apple hardware.

---

## Task batches and dependencies

```
Batch A (data model — everything depends on this)
  08-01  Device model: name, display_mode, mcp_exposed + Alembic migration
  08-02  Device-create + DevicePublic schema wiring for the four axes

Batch B (framebuffer fixes — the core bug)
  08-03  Linux: Xvfb in the container; DISPLAY=:0 actually resolves
  08-04  Windows: QEMU virtio-vga (drop -display none) so GDI+ capture works
  08-05  macOS (Apple-gated): QEMU virtio-gpu display adapter stop-gap
  08-06  Framebuffer self-check: per-family "is the screen capturable?" probe

Batch C (Host Resource Ledger — extends Phase 07 scheduler)
  08-07  ResourceLedger: durable committed-vs-total RAM/vCPU/disk accounting
  08-08  Reservation lifecycle: admit / reclaim-on-sleep / release-on-terminate
  08-09  Startup reconciliation of ledger vs psutil/hypervisor reality

Batch D (per-device log bus)
  08-10  DeviceLogEvent model + DeviceLogBus (ring buffer + redaction)
  08-11  Emit lifecycle/provisioner/transport/MCP events into the bus
  08-12  WS/SSE route: GET /api/v1/devices/{id}/logs/stream (loopback only)

Batch E (docs)
  08-13  Update local-hosting docs: framebuffer model, headless≠no-framebuffer, ledger
```

---

## Task 08-01: Device model — name, display_mode, mcp_exposed

**Files:** `apps/api/app/models.py` (edit `Device`), new Alembic migration under
`apps/api/alembic/versions/`.

Add to `Device`:
```python
name: str | None = Field(default=None, max_length=120)
display_mode: str = Field(default="headless", max_length=16)   # "headless" | "interactive"
mcp_exposed: bool = Field(default=True)
```
`display_mode` default `headless` (cheap, agent-first). `mcp_exposed` default `True` (agent-first).
Migration backfills existing rows: `name=NULL`, `display_mode='headless'`, `mcp_exposed=True`.

**Tests:** `test_device_defaults_headless_mcp_on`, `test_migration_backfills_existing_devices`.

**Do not:** add streaming fields here (Phase 09); do not add snapshot/name to `Snapshot` (Phase 10).

---

## Task 08-02: Create + public schema wiring for the four axes

**Files:** `apps/api/app/models.py` (`DeviceCreate`, `DevicePublic`), device-create route/service.

Extend `DeviceCreate` with `name: str | None`, `location: str = "local"`, `display_mode: str =
"headless"`, `mcp_exposed: bool = True`. Surface all four (+ `name`) on `DevicePublic`. The
create-from-snapshot path is Phase 10 — here only the "New" axes are wired. `DevicePublic.title`
helper returns `name or f"{family} · {id8}"` (D-6 fallback).

**Tests:** `test_create_device_accepts_four_axes`, `test_device_public_title_falls_back`.

**Do not:** validate OS/family availability here — that already flows through Phase 07 placement +
manifest filtering; reuse it.

---

## Task 08-03: Linux — Xvfb inside the container

**Files:** `apps/api/app/adapters/linux/local_provision.py` (edit), small entrypoint script asset.

Start `Xvfb :0 -screen 0 1920x1080x24` (configurable from template `extra_config.resolution`) as
the container's first process and export `DISPLAY=:0`, so the hardcoded `DISPLAY=:0` in
`linux/interaction.py`, `recording.py`, `system_ops.py` resolves. Prefer baking Xvfb + a tiny WM
(`fluxbox`/`openbox`) into the local image; fall back to installing at boot when absent. Capacity:
add the framebuffer's modest RAM to the device's ledger reservation (08-07).

**Tests:** `test_linux_local_starts_xvfb`, `test_linux_local_screenshot_returns_nonempty_png`
(skip when Docker absent). The screenshot test is the regression guard for the original gap.

**Do not:** add GStreamer/streaming here — only make the framebuffer exist and be capturable.

---

## Task 08-04: Windows — QEMU virtio-vga (remove `-display none`)

**Files:** `apps/api/app/adapters/windows/local_provision.py` (edit `_build_qemu_cmd`).

Replace `-display none` with a real display adapter: `-device virtio-vga` (or `-vga std`) plus
`-display none`'s headless equivalent that **still emulates a GPU** — i.e. keep no host window
(`-display vnc=127.0.0.1:<alloc>` for the VNC-bridge in Phase 09, or `-nographic`-free headless GL
later) but give the guest a scanout so `PrimaryScreen.Bounds` is non-zero and GDI+ `CopyFromScreen`
returns real pixels. Allocate a VNC display port from the ledger-tracked range and store it in
`provider_ids`.

**Tests:** `test_windows_qemu_cmd_has_display_adapter`, `test_windows_qemu_cmd_no_blind_display_none`.

**Do not:** build the VNC→WebRTC bridge here (Phase 09). Just guarantee a guest framebuffer exists.

---

## Task 08-05: macOS — QEMU virtio-gpu display adapter (Apple-gated stop-gap)

**Files:** `apps/api/app/adapters/macos/local_provision.py` (edit `_build_qemu_cmd`).

Same fix as Windows: give the guest a display device so WindowServer starts and `screencapture`
(stop-gap) produces real pixels. Remains hard-refused on non-Apple hardware (`PlacementError`).
**Note in the docstring** that Phase 09 replaces this entire path with Virtualization.framework
(`vz`) + ScreenCaptureKit on Apple Silicon (D-5); this task is the bridge so macOS isn't blind in
the interim.

**Tests:** `test_macos_qemu_cmd_has_display_adapter`, `test_macos_local_still_refused_on_non_apple`.

**Do not:** introduce `vz` here.

---

## Task 08-06: Framebuffer self-check probe

**Files:** `apps/api/app/services/local/framebuffer_probe.py` (new); hook into FSM
`bootstrapping_agent → ready`.

Per family, a fast "can I capture a non-empty frame?" check (Linux: `xdpyinfo` + 1px `scrot`;
Windows/macOS: dimensions > 0; Android: `adb` framebuffer present; iOS-sim: `simctl io` ok). On
failure, transition to `failed: framebuffer_unavailable` with an actionable message instead of
silently producing blank screenshots. Emits a log-bus event (08-11).

**Tests:** `test_probe_passes_on_live_framebuffer`, `test_probe_fails_to_state_framebuffer_unavailable`.

**Do not:** make it slow or networked; it's a sub-second gate.

---

## Task 08-07: ResourceLedger — durable committed-vs-total accounting

**Files:** `apps/api/app/services/local/ledger.py` (new); extends
`services/local/scheduler.py`; new `HostReservation` table in `models.py` + migration.

```python
@dataclass(frozen=True)
class ResourceClaim:
    ram_mb: int
    vcpu: float
    disk_mb: int

class ResourceLedger:
    def totals(self) -> ResourceClaim: ...          # from HostCapabilities minus reserved headroom
    def committed(self) -> ResourceClaim: ...        # sum of live HostReservation rows
    def can_admit(self, claim: ResourceClaim) -> bool: ...
    def reserve(self, device_id, claim) -> None: ...
    def release(self, device_id) -> None: ...
    def reclaim_ram(self, device_id) -> None: ...    # sleep: free RAM, keep disk
```
`HostReservation(device_id, ram_mb, vcpu, disk_mb, state)` persists so the ledger survives restarts.
Reserve a configurable **headroom** (default 20% RAM) for the host OS — never commit it.

**Tests:** `test_can_admit_rejects_over_ram`, `test_reclaim_ram_frees_only_ram`,
`test_headroom_is_never_committed`.

**Do not:** implement queueing (reject-fast, mirrors Phase 07 07-04). No cloud accounting — local only.

---

## Task 08-08: Reservation lifecycle wiring

**Files:** edit `services/device_fsm.py`, device-create, terminate, and (stub) sleep/wake hooks.

`provisioning` entry → `ledger.reserve(template_claim)`; reject → `preflight_blocked:
insufficient_host_resources`. `terminated` → `ledger.release`. Define the **sleep/wake seam**
(`reclaim_ram` on sleep, `reserve`-RAM on wake) as no-op-safe hooks Phase 10 fills in. Emits
ledger log-bus events.

**Tests:** `test_provision_reserves_then_terminate_releases`, `test_sleep_hook_reclaims_ram`,
`test_overcommit_blocks_at_preflight`.

**Do not:** implement actual VM suspend (Phase 10) — just the ledger side of the hook.

---

## Task 08-09: Startup reconciliation of the ledger

**Files:** edit `services/local/reconcile.py` (the Phase 07 reconciler).

On boot, rebuild ledger commitments from live `Device` rows and probe actual usage (`psutil`,
container/VM presence). Drop reservations for devices that no longer exist; log drift. Prevents
leaked reservations after a crash.

**Tests:** `test_reconcile_drops_reservation_for_dead_device`,
`test_reconcile_keeps_reservation_for_live_device`.

**Do not:** kill devices here — reconcile accounting only (Phase 07 already handles lost devices).

---

## Task 08-10: DeviceLogEvent model + DeviceLogBus

**Files:** `apps/api/app/models.py` (`DeviceLogEvent` table + `DeviceLogEventPublic`);
`apps/api/app/services/device_log_bus.py` (new).

```python
class DeviceLogEvent(SQLModel, table=True):
    id: uuid.UUID = ...
    device_id: uuid.UUID = Field(index=True)
    ts: datetime = ...
    level: str          # debug|info|warn|error
    source: str         # lifecycle|provisioner|transport|stream|mcp|recording|snapshot|ledger
    message: str
    fields_json: str | None   # structured extras, secret-redacted
```
`DeviceLogBus`: in-memory per-device bounded ring buffer (default 1000) + async pub/sub for live
subscribers + best-effort persist of last N to DB. A **redactor** strips SecretRef values, tokens,
and obvious secret patterns before anything is stored or emitted (D-4 / no-plaintext invariant).

**Tests:** `test_log_bus_ringbuffer_evicts_oldest`, `test_log_bus_redacts_secrets`,
`test_log_bus_fanout_to_subscribers`.

**Do not:** stream plaintext secrets; do not block device operations on log persistence (best-effort).

---

## Task 08-11: Emit events into the bus

**Files:** edit FSM, provisioners (Linux/Android/Windows/macOS/ios_sim `local_provision.py`),
`transport/*` channels, `mcp/dispatch.py`.

Wire emitters: FSM transitions (`source=lifecycle`); provisioner subprocess stdout/stderr line-tagged
(`source=provisioner`); channel `exec` command names — args redacted — and exit codes
(`source=transport`); MCP tool calls with role + decision (`source=mcp`, cross-link `Evidence`).
Keep emitters cheap and fire-and-forget.

**Tests:** `test_fsm_transition_emits_log`, `test_transport_exec_emits_redacted_command`,
`test_mcp_call_emits_with_decision`.

**Do not:** emit per-frame stream data (too noisy) — stream events are session-level (negotiate/
reconnect/bitrate), added in Phase 09.

---

## Task 08-12: WS/SSE log-stream route

**Files:** `apps/api/app/api/routes/device_logs.py` (new); register in router.

`GET /api/v1/devices/{id}/logs/stream` — WebSocket (preferred) with SSE fallback. On connect, replay
the ring buffer then stream live. **Bind to loopback only** (localhost-only invariant); reuse local
operator auth. Supports `?level=` and `?source=` filters and `?since=` cursor.

**Tests:** `test_log_stream_replays_then_live`, `test_log_stream_rejects_non_loopback`,
`test_log_stream_filters_by_source`.

**Do not:** expose externally; no multi-tenant fan-out (single local operator).

---

## Task 08-13: Docs

**Files:** edit `docs/operations/local-hosting.md`, `docs/operations/local-host-prerequisites.md`.

Document: the framebuffer model per family (and that **headless ≠ no framebuffer**, D-2); Xvfb /
virtio-vga prerequisites; the Host Resource Ledger (budget, headroom, reclaim-on-sleep); the
per-device log feed and how to tail it. Add an `Xvfb` row to the Linux prereqs.

---

## Exit criteria

- A `location=local` device of every supported family produces a **non-empty** screenshot through
  the existing MCP `screenshot` tool — the original framebuffer gap is closed and regression-tested.
- Devices carry `name`, `display_mode`, `mcp_exposed`; defaults are headless + MCP-on; existing rows
  migrate cleanly.
- Creating more devices than host RAM allows is refused at `preflight_blocked:
  insufficient_host_resources`; sleeping a device frees its RAM in the ledger; a control-plane
  restart reconciles the ledger without leaking reservations.
- `GET /devices/{id}/logs/stream` replays + streams structured, secret-redacted events on loopback.
- No streaming and no UI screen pane shipped (correctly deferred to Phases 09/11).
