---
doc_id: "7.5"
title: "ADR-0003 local hosting architecture"
section: "ADR"
status: "proposed"
updated: "2026-06-01"
---

# 7.5 — ADR-0003: Local hosting architecture (transport abstraction + resource scheduling + placement)

**Status:** Proposed

**Date:** 2026-06-01

## Context

DeviceLab today provisions every device family into the user's AWS account and reaches each guest over a single transport: SSM RunCommand (or `adb` tunneled through it). This is the BYOC cloud path and it works.

A recurring user need is to host device families **directly on the local host machine** — the developer's own laptop or workstation — with no cloud account at all. The motivating cases:

- **Cost and latency.** A local Linux device starts in ~2 seconds and costs nothing; the equivalent EC2 path is minutes and dollars.
- **Offline / air-gapped work.** Some users cannot or will not attach an AWS account.
- **The host OS is itself variable.** The control plane must run on a Linux, macOS, *or* Windows host, and the set of device families it can offer depends on what that host physically supports.

The current architecture cannot express any of this. Three structural gaps block it:

1. **Transport is hard-wired to SSM.** The adapter conflates *what the guest is* (Linux, Windows…) with *how the control plane talks to it* (SSM). A local Linux container is the same guest reached over `docker exec` — there is nowhere to express that without `if local:` branches scattered through every adapter.
2. **There is no resource ceiling.** Cloud capacity is effectively infinite (you pay). A laptop is not. Nothing today refuses or queues a `provision` that would oversubscribe host RAM/CPU/disk.
3. **There is no notion of *where* a device lives.** A device is implicitly always cloud. There is no placement attribute, so local/cloud cannot coexist behind one interface.

Apple's hardware constraint is a hard physical wall that no abstraction removes: **macOS and iOS Simulator can only run on Apple hardware**, locally or in cloud. This bounds what "any host OS" can mean.

This must be decided now because Phase 06 just stabilized the adapter SPI. Introducing local hosting later without a transport seam would force a second, more expensive SPI break.

## Decision

DeviceLab adds local hosting through **three new seams**, leaving the MCP gateway, manifest filtering, permissions, and observation/action envelopes unchanged.

### 1. Channel SPI — separate transport from adapter

Introduce a `Channel` abstraction distinct from `DeviceAdapter`. The adapter decides *what command/observation is needed*; the channel decides *how it reaches the guest*.

```
Channel (ABC): exec(), push_file(), pull_file(), heartbeat(), close()
  ├── SSMChannel        (cloud — existing behavior, extracted)
  ├── DockerExecChannel (local Linux — docker SDK exec)
  ├── ADBChannel        (local/cloud Android — adb direct or tunneled)
  └── SSHChannel        (local Windows/macOS VMs — paramiko/asyncssh)
```

A device carries a `location` (`local` | `cloud`) and a resolved channel. Adapters request a channel from a `ChannelFactory` keyed on `(family, location)` rather than constructing SSM calls inline.

### 2. Local resource scheduler — admission control + reaper

Add a `LocalScheduler` that the FSM consults before `provisioning`:

- Maintains a **host capacity model** (total vs committed RAM, vCPU, disk).
- **Admission control:** a `provision` that would oversubscribe is rejected into a new FSM reason `preflight_blocked: insufficient_host_resources` (or queued, configurable).
- **Reaper:** periodic GC of orphaned containers, leaked VM disk images, and dangling AVDs created by DeviceLab (matched by the existing `DeviceLab:*` tagging convention, extended to local label conventions).

### 3. Placement layer — `location` as a first-class device attribute

A device gains `location` and an optional placement policy (`prefer_local`, `local_only`, `cloud_only`). The MCP agent never sees or chooses transport; it asks for a device of a family and the placement policy + host capability decide where it lands. This is what unifies local and cloud behind one unchanged agent interface.

### Per-family local provisioner mapping (decision of record)

| Family | Local provisioner | Channel | Notes |
|---|---|---|---|
| linux | Docker container | DockerExecChannel | Primary local case; all host OSes via Docker Desktop |
| android | Android Virtual Device (AVD) process | ADBChannel | Needs host virtualization (KVM/WHPX/Hypervisor.framework) |
| windows | QEMU/libvirt or VirtualBox VM | SSHChannel | Heavier; cloud remains the recommended Windows path |
| macos | UTM/VMware VM **on Apple hardware only** | SSHChannel | Refused on non-Apple hosts |
| ios_sim | Xcode Simulator **on Apple hardware only** | (local exec) | Refused on non-Apple hosts |

### Host capability probing reuses the manifest-filtering pattern

The control plane probes the host (OS, CPU architecture, Docker present, virtualization available, Apple hardware?) and **filters the offered device families/templates** by host capability — the same mechanism already used to filter MCP tools by device capability, lifted one level up.

## Consequences

**Easier:**
- Local Linux devices become near-instant and free, the dominant day-one use case.
- Local and cloud unify behind one MCP surface; agents are placement-agnostic.
- The Channel seam removes `if local:` branching from adapters and is reusable for any future transport.
- Host-capability filtering falls out of the existing manifest machinery.

**Harder:**
- DeviceLab effectively becomes a minimal **hypervisor orchestrator** locally: scheduler, reaper, capacity admission, reconciliation. This is new surface area that did not exist in the pure-client cloud model.
- CPU **architecture (ARM vs x86)** becomes a real dimension on templates — Apple Silicon cannot run x86 Windows at usable speed, and Android/Linux images must be arch-matched.
- State must be **reconciled against hypervisor reality** on every control-plane restart, because laptops sleep/reboot/lose power mid-session in ways cloud instances do not.
- Image/asset supply chain (multi-GB VM disks, AVD system images) needs caching and pre-fetch to keep first-run provisioning tolerable.

**Risks accepted:**
- Windows-local via VM is slow and fragile relative to cloud; we accept this and steer users to the cloud Windows path as primary.
- The local scheduler is deliberately minimal and will not match a real orchestrator's sophistication; we accept simple admission + reaping over a full bin-packing scheduler.
- mitmproxy CA-cert injection differs per family and is not yet designed (tracked as an open question).

**Follow-up work:**
- Phase 07 implementation plan (`docs/roadmap/phases/phase-07-local-hosting.md`).
- Resolve OQ-011 (CPU architecture as a template dimension) and OQ-012 (per-family local proxy/CA injection) before the networking batch.

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| One container per device for **all** families (including Windows/macOS) | Containers share the host kernel; Windows containers require a Windows host, and macOS cannot be containerized at all. A single container model is physically impossible across families. |
| Keep SSM-only and emulate it locally with a tiny SSM-compatible shim per guest | Reimplements an AWS-internal protocol for no benefit; far more code than a `Channel` seam and still needs the scheduler/placement layers. |
| Branch inside each adapter (`if location == "local"`) instead of a Channel SPI | Scatters transport logic across every adapter, duplicates exec/file/heartbeat handling N times, and guarantees drift — exactly the coupling the SPI was created to prevent. |
| Local-only product (drop cloud) or cloud-only (drop local) | Each abandons a real, stated user need; the placement layer is specifically what lets both coexist without forcing the choice. |

## References

- `apps/api/app/adapters/spi.py` — adapter contract the Channel seam sits beside
- `apps/api/app/services/device_fsm.py` — FSM that the scheduler gates `provisioning` on
- `apps/api/app/mcp/manifest.py` — capability-filtering pattern reused for host-capability filtering
- `docs/operations/os-licensing.md` — Apple-hardware and Windows-license constraints that bound local hosting
- ADR-0002 (`0002-devicelab-product-default-overrides.md`) — local-first / BYOC posture this extends
- `docs/open-questions.md` — OQ-011 (ARM/x86 dimension), OQ-012 (local proxy/CA injection)
