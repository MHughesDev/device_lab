---
doc_id: "ops.local-hosting"
title: "Local Hosting Operator Guide"
section: "Operations"
updated: "2026-06-01"
---

# Local Hosting Operator Guide

DeviceLab can run device families directly on your laptop or CI runner — no AWS account required. This document covers the concepts, placement policy, and day-to-day operations. For OS-specific prerequisites (packages, BIOS flags, disk images) see [local-host-prerequisites.md](local-host-prerequisites.md).

---

## How it works

The `location` attribute on a `Device` row determines where it runs:

| `location` | Where the device lives | Transport |
|------------|----------------------|-----------|
| `cloud`    | AWS EC2 / Dedicated Host | SSMChannel over AWS Systems Manager |
| `local`    | Your machine | DockerExecChannel (Linux), ADBChannel (Android), SSHChannel (Windows/macOS), LocalShellChannel (iOS Sim) |

The MCP surface, observation envelopes, and action schemas are identical for both locations. Agents do not need to know where a device is running.

---

## Placement policy

Set `placement_policy` when creating a device:

| Policy | Behavior |
|--------|----------|
| `prefer_local` | Use local if the host supports the family; fall back to cloud otherwise |
| `local_only` | Fail with 4xx if the host cannot host this family |
| `cloud_only` | Always cloud, regardless of host capabilities |

Default is `prefer_local`.

### What "host can support" means per family

| Family | Linux host | macOS host (Apple HW) | macOS host (non-Apple) | Windows host |
|--------|-----------|----------------------|----------------------|--------------|
| `linux` | ✓ Docker | ✓ Docker | ✓ Docker | ✓ Docker |
| `android` | ✓ AVD (KVM) | ✓ AVD (HVF) | ✓ AVD (HVF) | ✓ AVD (WHPX) |
| `windows` | ✓ QEMU/KVM | ✗ no x86 on arm64 | ✓ QEMU/HVF | ✓ QEMU/WHPX |
| `macos` | ✗ | ✓ QEMU/HVF | ✗ non-Apple | ✗ |
| `ios_sim` | ✗ | ✓ xcrun simctl | ✗ non-Apple | ✗ |

---

## Admission control

Before a local device enters `provisioning`, the `LocalScheduler` checks available RAM and disk against safety reserves:

- RAM reserve: 512 MB (always kept for the OS and control plane)
- Disk reserve: 1 GB

If the request would exceed available capacity, the FSM transitions to `preflight_blocked: insufficient_host_resources` and the provision call returns a 4xx. No queue — reject-fast is the v1 policy.

Check current scheduler state via the API:

```
GET /api/v1/local/scheduler/snapshot
```

---

## Running diagnostics

```bash
devicelab doctor
```

Checks: Docker daemon, KVM/HVF/WHPX virtualization, disk space, ADB, xcrun/simctl, QEMU binary, control-plane port. Each check shows a status and an actionable remedy on failure.

---

## Resource cleanup

A periodic reaper sweeps Docker containers and AVDs that have a `devicelab.device` label but no corresponding live `Device` row (orphans from crashed or interrupted sessions).

Trigger a manual reap:

```
POST /api/v1/local/reaper/run
```

The reaper **never** touches containers or VMs without a DeviceLab label.

---

## Startup reconciliation

On each control-plane start, DeviceLab reconciles all non-terminal `location=local` Device rows against actual resource state:

- Container/emulator/VM still running → device re-adopted, state unchanged.
- Resource gone → device marked `failed` with `phase=lost_on_restart`.

This prevents stale rows accumulating across restarts.

---

## Networking and proxy

Local proxy / mitmproxy CA-cert injection is **not yet available** (blocked on OQ-012). Until that is resolved, `network: ["proxy", "capture"]` capabilities are unavailable for local devices. Cloud devices are unaffected.

---

## Supported local configurations at a glance

| Family | Provisioner | Channel | Host requirement |
|--------|------------|---------|-----------------|
| Linux | Docker container (ubuntu:24.04) | DockerExecChannel | Docker daemon |
| Android | AVD via avdmanager + emulator | ADBChannel | Android SDK + KVM/HVF/WHPX |
| Windows | QEMU VM (.qcow2 image) | SSHChannel | QEMU + KVM/WHPX; not arm64 macOS |
| macOS | QEMU VM (.qcow2 image) via HVF | SSHChannel | Apple Silicon or Intel Mac |
| iOS Sim | xcrun simctl | LocalShellChannel | Apple hardware + Xcode |

---

## Display model — headless ≠ no framebuffer (Phase 08)

Every local device has a **real framebuffer** regardless of `display_mode`:

| `display_mode` | Framebuffer | WebRTC stream | Human sees |
|----------------|-------------|---------------|------------|
| `headless` (default) | ✓ present | ✗ not started | Log panel only; "Attach interactive session" button |
| `interactive` | ✓ present | ✓ live | Full screen, audio, input control |

MCP tools (`screenshot`, `recording`, `ax_tree`) read the framebuffer **directly** (via OS-native capture) — they work in both modes and do not depend on a running WebRTC stream. Headless means *not streamed to a human*, not *no framebuffer*.

### Per-family framebuffer implementation

| Family | Virtual display | Notes |
|--------|----------------|-------|
| `linux` | `Xvfb :0 -screen 0 1920x1080x24` | Started as container first process; `DISPLAY=:0` exported |
| `android` | Android emulator virtual screen | Always present when AVD is booted |
| `windows` | QEMU `-device virtio-vga` + VNC loopback | Replaces the old `-display none` (Phase 08 bug fix) |
| `macos` | QEMU `-device virtio-gpu` + VNC loopback | Stop-gap; Phase 09 replaces with Virtualization.framework |
| `ios_sim` | Simulator framebuffer via `simctl` | Capture via `xcrun simctl io` |

### Framebuffer probe

Before a device transitions to `ready`, a sub-second **framebuffer self-check** probes whether the display is capturable:
- Linux: `xdpyinfo` against `DISPLAY=:0` inside the container
- Windows/macOS: VNC port reachable on loopback
- Android: SurfaceFlinger probe via `adb`
- iOS Sim: `simctl io` screenshot test

On failure the device transitions to `failed: framebuffer_unavailable` with an actionable message rather than silently producing blank screenshots.

---

## Four-axis device model (Phase 08)

Devices carry four independent axes set at creation time:

| Axis | Values | Default | Toggleable at runtime? |
|------|--------|---------|------------------------|
| `name` | `str \| None` (≤120 chars) | `None` | Yes (rename) |
| `display_mode` | `headless \| interactive` | `headless` | Yes ("Attach/Detach interactive session") |
| `mcp_exposed` | `bool` | `True` | Yes |
| `location` | `local \| cloud` | `local` | No |

`DevicePublic.title` returns `name` if set, otherwise `<family> · <id8>`.

---

## Host Resource Ledger (Phase 08)

The **Host Resource Ledger** extends the Phase 07 LocalScheduler into a durable, DB-persisted accounting layer:

- Every device template declares RAM/vCPU/disk requirements (defaults by family; see `_FAMILY_RESOURCE_DEFAULTS` in `device_fsm.py`).
- On `provisioning` entry the ledger writes a `HostReservation` row for the device.
- On `terminated` the reservation is deleted.
- A device holds its **full reservation** from `provisioning` until `terminated` — there is no intermediate suspended state.
- Headroom: **20% of total RAM** is permanently reserved for the host OS and is never committed to devices.
- If a create request would over-commit RAM, vCPU, or disk the FSM transitions to `preflight_blocked: insufficient_host_resources` before provisioning begins.

### Startup reconciliation

On control-plane restart the ledger is rebuilt from live `Device` rows via `reconcile_ledger()`:
- Live non-terminal devices → reservation (re-)written.
- Orphaned `HostReservation` rows (device gone or terminal) → deleted.

This prevents leaked reservations after a crash.

---

## Per-device log bus (Phase 08)

Every device emits a **structured, secret-redacted event stream** (`DeviceLogEvent`) consumed by:
- `GET /api/v1/devices/{id}/logs` — recent persisted events (HTTP/JSON)
- `WS /api/v1/devices/{id}/logs/stream` — replay ring buffer then stream live

### Event sources

| `source` | Events emitted |
|----------|---------------|
| `lifecycle` | FSM state transitions |
| `provisioner` | Container/VM start, install steps |
| `transport` | `exec` command summaries and exit codes (args redacted) |
| `mcp` | Tool invocations with role and allow/deny decision |
| `ledger` | Resource reservation and release events |
| `stream` | (Phase 09) Negotiate, ICE state, bitrate change, reconnect |

**Secrets are redacted** before any event is stored or emitted. The redactor strips AWS keys, bearer tokens, passwords, and other obvious secret patterns. Never put plaintext secrets in the log bus.

### Tail logs with query params

```
WS /api/v1/devices/{id}/logs/stream?level=warn&source=lifecycle&since=2026-06-01T00:00:00Z
```
