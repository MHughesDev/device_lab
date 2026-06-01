---
doc_id: "26.1"
title: "Streaming: Cloud vs Local capture-locus divergence"
section: "Design"
status: "stub"
updated: "2026-06-01"
---

# Streaming: Cloud vs Local Capture-Locus Divergence

## Problem

For local devices (Linux container, Windows/macOS QEMU/vz VMs), DeviceLab controls the
hypervisor directly — so capture can happen at the host level without an in-guest agent
(GStreamer ximagesrc / VNC rfbsrc / vz ScreenCaptureKit + sidecar).

For cloud devices (EC2), **the hypervisor is owned by AWS**, so host-side capture is
impossible. Capture **must** happen inside the guest using the OS-native capture API.

## Cloud capture path (per family)

| Family | In-guest capture | Encode | NAT traversal |
|--------|-----------------|--------|---------------|
| Linux (EC2) | Selkies (GStreamer WebRTC) or AWS DCV | GPU via NVENC / VA-API | coturn in user VPC |
| Windows (EC2) | Windows Desktop Duplication API in-guest agent | NVENC | coturn in user VPC |
| macOS (EC2 Mac Dedicated Host) | ScreenCaptureKit in-guest agent | VideoToolbox | coturn in user VPC |

## ICE topology

```
Local: loopback only — no STUN, no TURN (hosts are same machine)
Cloud: STUN (srflx) + coturn TURN in user VPC (BYOC; user provisions coturn EC2)
```

## In-guest agent protocol

Cloud devices run a lightweight in-guest agent that:
1. Captures the display via the native API
2. Encodes with the GPU (NVENC / VideoToolbox / VA-API)
3. Streams H.264 AUs over a secure tunnel to the DeviceLab API (loopback not available)
4. Receives input events (pointer/key) and injects via the native HID stack

This is the **cloud** path. Local delivery does not require it.

## ADR

See `docs/design/adr/adr-0007-coturn-cloud-turn.md` for the TURN infrastructure decision.

## Status

Cloud streaming is scoped and stubbed in Phase 09. Full implementation is a follow-on
once local streaming is proven. In-guest agent stubs live in `adapters/*/stream_cloud.py`.
