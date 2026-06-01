---
doc_id: "ADR-0006"
title: "Virtualization.framework (vz) for local macOS VMs on Apple Silicon"
status: "accepted"
date: "2026-06-01"
deciders: ["mhughesdev"]
---

# ADR-0006: Virtualization.framework (vz) for local macOS VMs on Apple Silicon

## Status

Accepted

## Context

macOS VMs provisioned locally need a real Metal-backed framebuffer for interactive
streaming. QEMU macOS (Phase 08 stop-gap) uses virtio-gpu + VNC, which adds a VNC
hop and lacks GPU acceleration on Apple Silicon.

On Apple Silicon, Apple's Virtualization.framework (`vz`) provides:
- `VZMacGraphicsDeviceConfiguration` — real Metal framebuffer, no VNC
- `VZVirtualMachineView` — native display attachment
- `VZVirtioGraphicsDeviceConfiguration` — HW-accelerated guest GPU
- `VZVirtioSoundDeviceConfiguration` — guest audio device

## Decision

Use **Virtualization.framework** as the default macOS-local provisioner on Apple Silicon.
Python calls a thin **Swift sidecar** process (`devicelab-vz-sidecar`) over a typed
Unix socket RPC. The sidecar owns the VZVirtualMachine lifecycle; Python owns policy.

Capture: **ScreenCaptureKit** (filtered to the VM display) + **VideoToolbox** H.264 encode.
Input: `VZVirtualMachineView`'s virtual HID path via the sidecar RPC.
Audio: `VZVirtioSoundDevice` → host CoreAudio → AVAudioEngine → Opus (Phase 09-16).

The QEMU macOS path remains a fallback (set `vz: false` in provider_ids or on Intel hosts).
Hard-refused on non-Apple-Silicon (Intel/Linux) hosts.

## Consequences

- Requires macOS 13+ (Ventura) for ScreenCaptureKit and vz macOS guests.
- The Swift sidecar must be compiled and placed in `$PATH` as `devicelab-vz-sidecar`.
- Sidecar RPC is a typed binary framing protocol (tag + length-prefixed JSON payload).
- The sidecar process must have `com.apple.security.virtualization` entitlement.
- Screen recording permission (TCC) must be granted to the sidecar.

## Alternatives considered

- **QEMU + VNC**: works on Intel/Linux; remains fallback. VNC adds latency and lacks
  GPU acceleration on Apple Silicon.
- **PyObjC direct call**: PyObjC bindings for VZVirtualMachine exist but are incomplete
  for the Metal display path; Swift sidecar is cleaner and more maintainable.
