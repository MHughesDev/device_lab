---
doc_id: "26.0"
title: "Low-latency streaming — design (dream build)"
section: "Design"
status: "reference"
updated: "2026-06-01"
---

# Low-Latency Screen Streaming — Design ("Dream Build")

Reference design behind Phases 08–12 (`docs/roadmap/interactive-workspace-plan.md`). Captures the
target architecture for hardware-accelerated, low-latency screen streaming + fast input injection,
and the precise local-vs-cloud divergence.

## Thesis

> Stop shipping lossless screenshots over a command channel. Ship a continuous, hardware-encoded
> video elementary stream into the WebRTC track that already exists — and where the virtualization
> layer lets you, capture *outside* the guest instead of running an agent inside it.

## What already exists (Phase 04)

- `stream/peer.py` (`StreamPeer` wraps `RTCPeerConnection`), `stream/gateway.py` (SDP negotiate /
  reconnect / JWT session tokens), `api/routes/stream.py`, and the SPI hook `spi.py:stream_offer()`.
- **Gap:** every `MediaStreamTrack` is a blank stub (`_BlankVideoTrack`) or returns `None`
  (`adapters/android/stream.py`). The only "live view" is poll-a-base64-PNG over MCP — the worst case
  for latency. The streaming *core is the right shape*; the media layer is missing.

## Latency anatomy

Glass-to-glass = capture + encode + packetize + network + jitter-buffer + decode + render. On
**local** (device + browser on the same host) network and jitter-buffer collapse to ~0, so latency is
*entirely* capture + encode + decode → **1–2 frames (~16–33 ms)** with hardware codecs. The whole
local design protects that budget.

## Unifying abstraction

A `MediaSource` / `InputSink` SPI dispatched on `(family, location)` — mirroring the existing
`ChannelFactory`. `StreamPeer` attaches `MediaSource.track()` and routes the input data channel to
`InputSink.inject()`. Signaling, tokens, reconnect, and the browser client never learn where the bits
originate. (Detailed in Phase 09, task 09-01.)

## Per-family target path (local)

| Family | Capture | Encode | Input |
|--------|---------|--------|-------|
| Android | scrcpy MediaCodec mirror → raw H.264 over adb | none (device GPU already encoded) | scrcpy control socket |
| Linux (Docker) | Xvfb `:0` + GStreamer `ximagesrc` | VA-API/NVENC → x264 `zerolatency` fallback | persistent `uinput`/XTEST daemon |
| Windows (QEMU) | hypervisor-side: VNC-bridge → (later) virtio-gpu-gl + dbus | host VA-API/NVENC | QMP `input-send-event` (no guest agent) |
| macOS (local) | Virtualization.framework `VZGraphicsDevice` + ScreenCaptureKit | VideoToolbox (HW) | `vz` virtual HID |
| iOS-sim | ScreenCaptureKit window capture | VideoToolbox | SimulatorKit/`simctl` HID |

Desktop families share one **GStreamer** capture+encode engine (swap `src`/`enc`); Android and
iOS-sim use device-native encoders.

## Local vs cloud divergence (the load-bearing distinction)

**Same everywhere:** signaling/`gateway.py`, JWT tokens, `StreamPeer`, the browser client, the input
wire protocol, and the MCP control plane.

**Divergent:**

| Axis | Local | Cloud | Why forced |
|------|-------|-------|-----------|
| **Capture locus** | hypervisor-side (QEMU dbus / `vz`) — no guest agent | **in-guest agent required** | On EC2 / Mac Dedicated Host **AWS owns the hypervisor** — you cannot capture from outside the guest |
| Encode location | host GPU (the laptop) | on the EC2 instance, GPU tier | keep encode next to the framebuffer |
| ICE | one `127.0.0.1` host candidate; no STUN/TURN | STUN + **coturn in user VPC** | loopback needs no traversal; honors localhost-only |
| Congestion / ABR | off — pin high CBR | transport-cc + dynamic res + (opt) SVC | loopback bandwidth is free |
| Jitter buffer | `playoutDelayHint≈0` | 20–60 ms | no jitter on loopback |
| Fan-out | single direct peer | optional SFU | one encode → many viewers |

≈70% shared, ≈30% per-`(family×location)` — exactly the `MediaSource`/`InputSink` registry.

## Encoder settings that win/lose "fast"

H.264 baseline (universal HW decode). `tune=zerolatency`, `bframes=0`, **intra-refresh instead of
periodic IDR keyframes** (kills the keyframe latency/bitrate spike — biggest single win),
slice-based. **Freeze-drop** to ~1fps on static screens (automation screens are mostly static).
`smooth` vs `sharp_text` profiles. Local pins high CBR; cloud uses capped CRF + transport-cc ABR.

## Browser side

Primary: WebRTC media track → `<video>` with `playoutDelayHint≈0` on local (one code path). Optional
local power-user fast-path: **WebCodecs → `<canvas>`** fed raw H.264 AUs over a data channel (bypasses
the RTP jitter buffer — the scrcpy-web pattern). Pointer-move coalesced on the unreliable channel;
keys/clicks on the reliable channel; binary framing.

## The one integration wrinkle

aiortc normally encodes raw frames itself; we have pre-encoded H.264 (Android/iOS/`vz`/GStreamer). We
add a thin **encoded-passthrough track** (`stream/encoded_track.py`, ~120 LOC) so aiortc packetizes
without re-encoding — keeping the locked aiortc dep and one WebRTC stack. Fallback (if it proves
brittle): GStreamer `webrtcbin` for media only, recorded in an ADR. Spiked first in task 09-02.

## Locked decisions (user-confirmed)

- **(A)** aiortc encoded-passthrough (not GStreamer `webrtcbin`).
- **macOS local → Virtualization.framework** on Apple Silicon (drop QEMU there).
- **QEMU capture → VNC-bridge first**, upgrade to GL+dbus+HW-encode where a host GPU exists.

## Acceptance budgets

Local HW < 50 ms (stretch 30 ms); local SW < 100 ms; cloud same-region < 150 ms (glass-to-glass).
Automated harness in task 09-16.
