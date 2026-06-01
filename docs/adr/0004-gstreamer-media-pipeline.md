---
doc_id: "ADR-0004"
title: "GStreamer for desktop capture and H.264 encode"
status: "accepted"
date: "2026-06-01"
deciders: ["mhughesdev"]
---

# ADR-0004: GStreamer for desktop capture and H.264 encode

## Status

Accepted

## Context

DeviceLab needs to capture and encode screen content from Linux containers (Xvfb)
and Windows QEMU VMs (VNC) for WebRTC streaming. The encode path must be:
- Hardware-accelerated (VA-API on iGPU, NVENC on NVIDIA)
- Low-latency (< 100ms software, < 50ms hardware)
- Available as a fallback on CPU-only hosts (x264enc)
- Decoupled from the WebRTC stack (aiortc handles transport)

## Decision

Use **GStreamer** with the Python `gi.repository.Gst` binding for all
desktop-family capture and encode pipelines. Encoder selection order:
1. `vaapih264enc` — Intel/AMD iGPU VA-API (widely available on Linux desktops)
2. `nvh264enc` — NVIDIA NVENC (datacenter and gamer GPUs)
3. `x264enc tune=zerolatency` — CPU fallback (always available)

The GStreamer pipeline outputs encoded H.264 access units into an `appsink`,
which delivers bytes to `EncodedVideoTrack.push_au()`. GStreamer is **not** used
for WebRTC transport — that remains aiortc.

## Consequences

- GStreamer and gst-plugins-bad must be present in the API container image.
  A runtime check (`is_gstreamer_available()`) falls back to a blank stream
  rather than crashing, enabling headless-only deployments.
- The `ximagesrc` element requires an X server (Xvfb, provided by Phase 08).
- The `rfbsrc` element (gst-plugins-bad) is needed for Windows VNC capture.
- The `GstPipeline` class runs in a background thread with a GLib MainLoop;
  frame bytes are dispatched back to the asyncio loop via `call_soon_threadsafe`.
- Do NOT use `webrtcbin` — aiortc is the locked WebRTC stack (spec.md invariant).

## Alternatives considered

- **FFmpeg** (`ffmpeg-python`): would work but GStreamer has better VA-API and
  easier Python integration for capture+encode without transcoding.
- **aiortc's built-in encode**: aiortc re-encodes raw frames; we need encoded
  passthrough to avoid double-encode latency and CPU overhead.
