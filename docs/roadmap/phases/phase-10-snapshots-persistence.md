---
doc_id: "25.3"
title: "Phase 10 — Snapshots & Persistence (local-first)"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-06-01"
---

# Phase 10 — Snapshots & Persistence (local-first)

**Progress: 0%** `░░░░░░░░░░` — planned

## Objective

Make "existing / snapshot devices" real: a named, reusable capture of a device's **OS + installed
apps/packages + (optionally) running state**, so a user can pick one from the create wizard and get
an instant, fully-provisioned device. Add **sleep/wake** that suspends a device and **reclaims its
RAM** through the Phase 08 ledger, and the **Create-from-snapshot** path. This is local-first; the
existing cloud/EBS-flavored `Snapshot` model is extended, not replaced.

Read first: `interactive-workspace-plan.md` (D-1 persistence axis, D-3 memory ledger, D-6 naming)
and `phase-08` (ResourceLedger, sleep/wake hooks).

---

## OSS / mechanisms pulled in this phase

| Family | Disk snapshot mechanism | RAM-state (sleep) mechanism |
|--------|-------------------------|------------------------------|
| Linux (Docker) | `docker commit` → image (or overlay layer) | `docker pause`/CRIU checkpoint (best-effort; fallback cold) |
| Android (AVD) | AVD snapshot / qcow2 of userdata | emulator snapshot save/load |
| Windows (QEMU) | qcow2 **overlay** (backing-file) | QEMU `savevm`/`migrate to file` (RAM state) |
| macOS (`vz`) | APFS/disk image copy or qcow2 overlay | `vz` `saveMachineState`/`restoreMachineState` |
| iOS-sim | `simctl clone` / data-container copy | n/a (framework-managed; cold restore) |

No new pip deps; all are CLI/system mechanisms documented in host-prerequisites. RAM-state restore is
**best-effort per family** with a clean fallback to cold boot from the disk snapshot.

---

## Task batches and dependencies

```
Batch A (model + library — everything depends on this)
  10-01  Extend Snapshot model: name, kind, family, location, storage_path, parent, ram_state
  10-02  SnapshotLibrary service + list/get/rename/delete + REST routes

Batch B (per-family disk snapshot create/restore — depends on A)
  10-03  Snapshot SPI hook on the adapter (create_snapshot / restore_snapshot)
  10-04  Linux snapshot (docker commit / overlay)
  10-05  Android snapshot (AVD/qcow2)
  10-06  Windows snapshot (qcow2 overlay backing-file)
  10-07  Apple-gated: macOS (vz/disk) + iOS-sim (simctl clone) snapshot

Batch C (create-from-snapshot — depends on A, B)
  10-08  Create-from-snapshot provisioning path + ledger reservation from snapshot size

Batch D (sleep / wake with RAM reclaim — depends on Phase 08 hooks, B)
  10-09  Sleep: suspend + persist RAM state (where supported) + ledger.reclaim_ram
  10-10  Wake: ledger re-reserve RAM (or refuse) + resume or cold-restore

Batch E (docs)
  10-11  Snapshot & persistence operator guide; per-family caveats + storage budgeting
```

---

## Task 10-01: Extend the Snapshot model

**Files:** `apps/api/app/models.py` (edit `Snapshot`, `SnapshotPublic`, add `SnapshotCreate`);
Alembic migration.

Add (keep existing cloud fields):
```python
name: str | None = Field(default=None, max_length=120)     # D-6
kind: str = Field(default="disk", max_length=16)            # "disk" | "ram_state"
location: str = Field(default="local", max_length=32)
storage_path: str | None = Field(default=None, max_length=1024)   # local image/overlay path
parent_snapshot_id: uuid.UUID | None = Field(default=None)        # overlay chain
ram_state: bool = Field(default=False)                            # captured RAM (sleep)
size_mb: int | None = Field(default=None)
```
`SnapshotPublic.title` → `name or f"{family} · {id8}"`.

**Tests:** `test_snapshot_defaults_local_disk`, `test_snapshot_public_title_fallback`,
`test_migration_preserves_cloud_snapshot_fields`.

**Do not:** break the existing cloud snapshot rows/fields (Phase 05 contract).

---

## Task 10-02: SnapshotLibrary service + routes

**Files:** `apps/api/app/services/snapshot_library.py` (new); `api/routes/snapshots.py` (extend).

`list/get/rename/delete` over workspace snapshots; `GET /api/v1/snapshots?location=local` powers the
"Existing" wizard list (returns `title`, `family`, `os`, `size_mb`, `created_at`). Delete frees disk
budget in the ledger and removes the on-disk image (idempotent). Rename sets `name` (D-6).

**Tests:** `test_library_lists_local_snapshots`, `test_rename_snapshot`,
`test_delete_snapshot_frees_disk_and_removes_image`.

**Do not:** delete an image that is a `parent_snapshot_id` of a live overlay — refuse with a clear
error.

---

## Task 10-03: Snapshot SPI hook

**Files:** `apps/api/app/adapters/spi.py` (edit `DeviceAdapter`).

Add optional methods (default `CapabilityUnsupportedError`):
```python
async def create_snapshot(self, device, name: str | None, ram_state: bool) -> dict: ...
async def restore_snapshot(self, snapshot, device, template) -> dict: ...
```
Declare `snapshot: bool` capability per family in the manifest. Mirrors the existing optional-method
pattern (`stream_offer`, `start_recording`).

**Tests:** `test_adapter_without_snapshot_raises_capability_unsupported`,
`test_manifest_declares_snapshot_capability`.

**Do not:** put family logic in core; each adapter implements its own mechanism (Batch B).

---

## Task 10-04: Linux snapshot

**Files:** `apps/api/app/adapters/linux/snapshot.py` (new); wire into `linux/adapter.py`.

`create_snapshot`: `docker commit` the container → a labeled local image (or export an overlay
layer), record `storage_path`/`size_mb`. `restore_snapshot`: provision a new container **from that
image** (reuses Phase 07 `local_provision` with an image override). `ram_state` via `docker
pause`+checkpoint when CRIU is available; else disk-only.

**Tests:** `test_linux_create_snapshot_commits_image`, `test_linux_restore_provisions_from_image`
(Docker-gated).

**Do not:** snapshot unlabeled/user containers (reaper label discipline from Phase 07).

---

## Task 10-05: Android snapshot

**Files:** `apps/api/app/adapters/android/snapshot.py` (new).

`create_snapshot`: emulator snapshot save (or qcow2 of userdata) → `storage_path`. `restore_snapshot`:
boot an AVD with `-snapshot`/loaded state. `ram_state` via emulator snapshot.

**Tests:** `test_android_create_snapshot_saves_state`, `test_android_restore_boots_from_snapshot`.

**Do not:** exceed disk budget without a ledger check.

---

## Task 10-06: Windows snapshot (qcow2 overlay)

**Files:** `apps/api/app/adapters/windows/snapshot.py` (new).

`create_snapshot`: `qemu-img create -f qcow2 -b <base>` overlay (or `qemu-img convert` for a flat
capture) → record `parent_snapshot_id`/`storage_path`. `restore_snapshot`: launch QEMU with the
overlay as the drive. `ram_state` via QEMU `savevm`/migrate-to-file.

**Tests:** `test_windows_snapshot_creates_overlay_with_backing`,
`test_windows_restore_launches_from_overlay`.

**Do not:** mutate the backing base image — overlays are copy-on-write.

---

## Task 10-07: Apple-gated snapshots (macOS + iOS-sim)

**Files:** `apps/api/app/adapters/macos/snapshot.py`, `apps/api/app/adapters/ios_sim/snapshot.py`
(new). Hard-refused on non-Apple hardware (`PlacementError`).

macOS: `vz` `saveMachineState` (RAM) or disk-image copy (disk); restore via `vz` restore or
overlay. iOS-sim: `simctl clone`/data-container copy for disk; cold restore only (no RAM state).

**Tests:** `test_macos_snapshot_refused_on_non_apple`, `test_ios_sim_clone_creates_snapshot`.

**Do not:** claim RAM-state for iOS-sim (cold restore only).

---

## Task 10-08: Create-from-snapshot provisioning path

**Files:** edit device-create service; `DeviceCreate` gains `snapshot_id: uuid.UUID | None`.

When `snapshot_id` is set ("Existing" wizard branch), inherit `family`/`os`/`location` from the
snapshot, **reserve RAM+disk from the ledger sized by the snapshot** (D-3), and dispatch to the
family `restore_snapshot`. The device starts in the same FSM but skips fresh-install bootstrap. Marks
`persistence=snapshot_backed`. The device inherits the snapshot's `name` unless the user supplies one.

**Tests:** `test_create_from_snapshot_inherits_family_and_reserves_ledger`,
`test_create_from_snapshot_skips_fresh_bootstrap`, `test_create_from_snapshot_refused_when_overcommit`.

**Do not:** allow create-from-snapshot to over-commit the ledger; refuse at `preflight_blocked`.

---

## Task 10-09: Sleep (suspend + RAM reclaim)

**Files:** `apps/api/app/services/device_power.py` (new); fills the Phase 08 sleep hook.

`POST /devices/{id}/sleep`: suspend the device (family `create_snapshot(ram_state=True)` or native
pause), then `ledger.reclaim_ram(device_id)` so the freed RAM is immediately available to other
devices (D-3). Sets `state=sleeping`. Disk reservation persists. Emits audit + log-bus events.

**Tests:** `test_sleep_suspends_and_reclaims_ram`, `test_sleep_keeps_disk_reservation`,
`test_sleeping_device_releases_ram_to_other_admits`.

**Do not:** lose the device's disk state; sleep must be resumable.

---

## Task 10-10: Wake (re-reserve + resume)

**Files:** `apps/api/app/services/device_power.py` (extend).

`POST /devices/{id}/wake`: `ledger` must re-reserve the RAM — if the host is now full, **refuse**
with `insufficient_host_resources` (the device stays `sleeping`, nothing is silently over-committed).
On success, resume from RAM state where supported, else cold-restore from the disk snapshot. Sets
`state=ready`.

**Tests:** `test_wake_refused_when_ram_unavailable`, `test_wake_resumes_from_ram_state`,
`test_wake_cold_restores_when_no_ram_state`.

**Do not:** wake without a successful ledger reservation.

---

## Task 10-11: Docs

**Files:** `docs/operations/snapshots-and-persistence.md` (new); cross-link
`docs/operations/local-hosting.md`.

Per-family snapshot/sleep capabilities + caveats; storage budgeting (overlay chains, dedup); the
ephemeral vs snapshot_backed model (D-1); how sleep frees RAM (D-3); naming (D-6).

---

## Exit criteria

- A user can **Save as snapshot** (named) from a running local device, see it in the snapshot
  library, and **Create-from-snapshot** to get a ready device that inherited OS + apps + state.
- Disk and RAM for snapshots and restores are reserved through the ledger; create-from-snapshot and
  wake are **refused** rather than over-committing host memory (D-3).
- **Sleep** suspends a device and returns its RAM to the ledger; **wake** re-reserves RAM (or refuses)
  and resumes (RAM-state) or cold-restores.
- Snapshots and devices carry user-editable `name`s used as titles/labels (D-6).
- Existing cloud `Snapshot` rows and Phase 05 behavior are unbroken.
