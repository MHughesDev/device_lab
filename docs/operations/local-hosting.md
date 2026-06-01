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
