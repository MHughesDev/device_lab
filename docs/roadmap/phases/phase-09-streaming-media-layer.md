---
doc_id: "25.2"
title: "Phase 09 — Low-Latency Streaming Media Layer"
section: "Roadmap"
status: "complete"
completion: "100%"
updated: "2026-06-01"
---

# Phase 09 — Low-Latency Streaming Media Layer

**Progress: 100%** `██████████` — complete

## Objective

Replace the blank/stub WebRTC tracks with **real, hardware-accelerated, low-latency** screen
streaming and **fast input injection**, behind a `MediaSource`/`InputSink` SPI that mirrors the
existing `ChannelFactory` `(family, location)` dispatch. Implement the user-locked decisions:
**(A)** aiortc encoded-passthrough (no second WebRTC stack), **`vz`+ScreenCaptureKit+VideoToolbox**
for macOS/iOS-sim local, and a **VNC-bridge-first** QEMU capture path. Wire the runtime
**attach/detach interactive session** toggle (display_mode `headless ⇄ interactive`). Cloud variants
(coturn, in-guest agents) are scoped but explicitly back-loaded.

Read first: `docs/design/streaming-dream-build.md` and `interactive-workspace-plan.md` (D-5).
This phase fills the existing `stream/peer.py`, `stream/gateway.py`, `api/routes/stream.py` shells
(Phase 04) — it does not rebuild them.

---

## OSS pulled in this phase (each needs an ADR)

| Package / source | What we take | Where it lands |
|------------------|--------------|----------------|
| **GStreamer** + `python-gst` | capture→encode pipeline (desktop families) | `stream/pipeline/gst.py`, per-family `stream_local.py` |
| **scrcpy-server** jar + `adb` | Android MediaCodec H.264 mirror + control | `adapters/android/stream_local.py`, `adapters/android/input.py` |
| **Virtualization.framework** (`vz`) | macOS VM with real framebuffer (Apple Silicon) | `adapters/macos/vz_provision.py` (+ Swift/PyObjC sidecar) |
| **ScreenCaptureKit** + **VideoToolbox** | macOS/iOS-sim live capture + HW encode | `adapters/macos/stream_local.py`, `adapters/ios_sim/stream_local.py` |
| **coturn** (cloud only) | NAT traversal in user VPC | `stream/ice.py` cloud branch; infra docs |
| aiortc encoded-passthrough shim (write from scratch) | feed pre-encoded H.264 into aiortc | `stream/encoded_track.py` |

ADRs required: `adr-00xx-gstreamer-media-pipeline.md`, `adr-00xx-scrcpy-android-stream.md`,
`adr-00xx-vz-macos-local.md`, `adr-00xx-coturn-cloud-turn.md`.

---

## Task batches and dependencies

```
Batch A (SPI + the hard integration spike — everything depends on these)
  09-01  MediaSource / InputSink SPI + factory ((family, location) registry)
  09-02  aiortc encoded-passthrough track (the spike — prove it on raw H.264)
  09-03  StreamPeer: attach MediaSource.track(); route input channel → InputSink
  09-04  ICE config split: local loopback-only vs cloud STUN+coturn

Batch B (Android — first real stream; depends on A)
  09-05  Android MediaSource via scrcpy-server (H.264 passthrough)
  09-06  Android InputSink via scrcpy control protocol

Batch C (Linux — GStreamer pipeline; depends on A, Phase 08 Xvfb)
  09-07  GStreamer pipeline builder (ximagesrc → x264/VA-API → appsink)
  09-08  Linux MediaSource + InputSink (uinput/XTEST daemon, no per-event spawn)

Batch D (Windows — VNC-bridge; depends on A, Phase 08 virtio-vga)
  09-09  VNC-bridge MediaSource (QEMU VNC → frames → encode)
  09-10  Windows InputSink via QMP input-send-event (hypervisor injection)

Batch E (Apple — vz + ScreenCaptureKit; depends on A; Apple-gated)
  09-11  vz macOS provisioner + sidecar RPC
  09-12  macOS MediaSource (ScreenCaptureKit→VideoToolbox) + InputSink
  09-13  iOS-sim MediaSource (ScreenCaptureKit window capture) + InputSink

Batch F (runtime control + quality + audio; depends on A–E as available)
  09-14  Attach/Detach interactive session (display_mode toggle, no reprovision)
  09-15  Display & quality profiles (resolution/fps, sharp-text vs smooth, freeze-drop)
  09-16  Audio track: device audio → Opus → WebRTC audio stream (per-family)
  09-17  Stream-session log-bus events + latency acceptance harness

Batch G (cloud variants — back-loaded; depends on A–C)
  09-18  Cloud capture-locus note + in-guest agent stubs + coturn config (ADR-gated)
```

---

## Task 09-01: MediaSource / InputSink SPI + factory

**Files:** `apps/api/app/stream/source.py` (new), `apps/api/app/stream/factory.py` (new).

```python
class MediaSource(ABC):
    async def start(self) -> None: ...
    def track(self) -> MediaStreamTrack: ...
    async def set_bitrate(self, bps: int) -> None: ...   # cloud ABR; no-op local
    async def request_keyframe(self) -> None: ...
    async def stop(self) -> None: ...

@dataclass
class InputEvent:
    kind: str           # pointer_move|pointer_down|pointer_up|key_down|key_up|scroll|text
    x: int | None; y: int | None; button: int | None
    key: str | None; text: str | None; reliable: bool

class InputSink(ABC):
    async def inject(self, ev: InputEvent) -> None: ...

def media_source_for(device) -> MediaSource: ...   # registry on (family, location)
def input_sink_for(device) -> InputSink: ...
```

**Tests:** `test_factory_dispatches_android_local`, `test_factory_unknown_pair_raises`,
`test_inputevent_pointer_move_is_unreliable_by_default`.

**Do not:** implement any concrete source here — registry + ABCs only.

---

## Task 09-02: aiortc encoded-passthrough track (the spike)

**Files:** `apps/api/app/stream/encoded_track.py` (new).

A `MediaStreamTrack` subclass that accepts **already-encoded H.264 access units** (from scrcpy /
MediaCodec / GStreamer appsink / VideoToolbox) and hands them to aiortc's RTP sender **without
re-encoding**. Implements the thin encoder-bypass aiortc lacks publicly (~120 LOC; wrap NAL units as
`av.Packet`, advertise H.264 in SDP, honor PLI/keyframe requests by forwarding to
`MediaSource.request_keyframe`). **This is the riskiest task — do it before per-family work.** If it
proves infeasible, the ADR records the fallback (GStreamer `webrtcbin` for the media path only).

**Tests:** `test_encoded_track_emits_packets_without_reencode`,
`test_encoded_track_forwards_pli_to_keyframe_request`, `test_sdp_advertises_h264`.

**Do not:** add VP9/AV1 here (H.264 baseline only this phase).

---

## Task 09-03: StreamPeer wiring

**Files:** edit `apps/api/app/stream/peer.py`, `apps/api/app/stream/gateway.py`.

Replace `_BlankVideoTrack` with `media_source_for(device).track()`. Route inbound `"input"`
data-channel messages → decode (binary protocol: pointer-move on unreliable/unordered; key/click on
reliable/ordered) → `input_sink_for(device).inject()`. Coalesce pointer-moves to latest. Start/stop
the `MediaSource` with the peer lifecycle. Keep negotiate/reconnect/JWT untouched.

**Tests:** `test_peer_attaches_real_track`, `test_peer_routes_input_to_sink`,
`test_pointer_moves_coalesced`.

**Do not:** change the signaling routes or token logic (Phase 04 contract is stable).

---

## Task 09-04: ICE config split (local vs cloud)

**Files:** `apps/api/app/stream/ice.py` (new); used by `gateway.negotiate`.

`location=local` → a single `127.0.0.1` host candidate, **no STUN, no TURN** (honors localhost-only
invariant; near-zero connect time). `location=cloud` → STUN (srflx) + **coturn** creds from settings
(Phase 12), deployed in the user's VPC (BYOC). Set `playoutDelayHint≈0` hint for local.

**Tests:** `test_ice_local_is_loopback_only`, `test_ice_cloud_includes_turn_when_configured`.

**Do not:** require TURN for local; never send local media off-host.

---

## Task 09-05: Android MediaSource (scrcpy passthrough)

**Files:** `apps/api/app/adapters/android/stream_local.py` (new; supersedes the
`adapters/android/stream.py` stub).

Launch `scrcpy-server` on the device, pull the raw **H.264** bitstream over the adb-forwarded
socket, feed access units into the `encoded_track` (09-02) — **no re-encode** (MediaCodec already
used the device GPU). Configurable bitrate/max-size/fps. This is the first end-to-end real stream
and the highest-value win.

**Tests:** `test_android_source_yields_h264_aus` (fixture/mock scrcpy), `test_android_source_stop_kills_server`.

**Do not:** use `adb screenrecord` (1–2s buffer, 180s cap) — scrcpy MediaCodec only.

---

## Task 09-06: Android InputSink (scrcpy control)

**Files:** `apps/api/app/adapters/android/input.py` (new).

Inject pointer/key/text/scroll via the scrcpy **control socket** (sub-frame latency) instead of
spawning `adb shell input` per event. Map `InputEvent` → scrcpy control messages; touch for
pointer, inject-keycode/text for keys.

**Tests:** `test_android_input_maps_pointer_to_touch`, `test_android_input_text_injection`.

**Do not:** fall back to per-event `adb shell input` on the hot path (keep the existing command-path
only as a degraded fallback when scrcpy control is unavailable).

---

## Task 09-07: GStreamer pipeline builder

**Files:** `apps/api/app/stream/pipeline/gst.py` (new).

Build low-latency H.264 pipelines, selecting the encoder by host capability:
`vaapih264enc` (iGPU) → `nvh264enc` (NVIDIA) → `x264enc tune=zerolatency` (CPU fallback). Enforce the
low-latency profile: `bframes=0`, **intra-refresh** (no periodic IDR spikes), slice-based,
`appsink` emits encoded AUs into `encoded_track`. Expose `set_bitrate`/`request_keyframe`.

**Tests:** `test_pipeline_picks_vaapi_when_present`, `test_pipeline_falls_back_to_x264`,
`test_pipeline_sets_zerolatency_no_bframes_intra_refresh`.

**Do not:** use `webrtcbin` (we keep aiortc, D-5/A); GStreamer is capture+encode only.

---

## Task 09-08: Linux MediaSource + InputSink

**Files:** `apps/api/app/adapters/linux/stream_local.py` (new), `adapters/linux/input.py` (new).

MediaSource: `ximagesrc` on the Xvfb `:0` (Phase 08) → pipeline (09-07) → `encoded_track`.
InputSink: a **persistent input daemon** in the container using `XTEST`/`uinput` reading decoded
events — **no per-event `xdotool` spawn** (the current `interaction.py` pattern is too slow for
interactive control; it remains for one-shot MCP actions).

**Tests:** `test_linux_source_captures_xvfb`, `test_linux_input_uses_persistent_daemon`.

**Do not:** regress the MCP one-shot action path; the daemon is additive for live control.

---

## Task 09-09: Windows VNC-bridge MediaSource

**Files:** `apps/api/app/adapters/windows/stream_local.py` (new).

Capture the QEMU **VNC** output (Phase 08 virtio-vga + `-display vnc=`) — GStreamer `rfbsrc` or a
small VNC client → pipeline (09-07) → `encoded_track`. This is the "works everywhere" path (D-5);
GL+dbus+HW-encode is a documented future upgrade for GPU hosts.

**Tests:** `test_windows_vnc_bridge_yields_frames` (mock VNC server),
`test_windows_source_stop_releases_vnc`.

**Do not:** require an in-guest capture agent for **local** Windows (hypervisor-side VNC suffices);
in-guest agents are the **cloud** path (09-17).

---

## Task 09-10: Windows InputSink via QMP

**Files:** `apps/api/app/adapters/windows/input.py` (new).

Inject mouse/keyboard at the **hypervisor** via QEMU **QMP `input-send-event`** (abs pointer + key) —
no in-guest agent, very low latency, pairs with VNC capture.

**Tests:** `test_windows_input_qmp_abs_pointer`, `test_windows_input_qmp_key`.

**Do not:** use PowerShell SendInput for local (that's the cloud in-guest path).

---

## Task 09-11: vz macOS provisioner + sidecar

**Files:** `apps/api/app/adapters/macos/vz_provision.py` (new); small Swift/PyObjC sidecar +
typed RPC; ADR `adr-00xx-vz-macos-local.md`.

On Apple Silicon, provision a macOS VM via **Virtualization.framework** (`VZVirtualMachine` +
`VZMacGraphicsDeviceConfiguration`) instead of QEMU — a real Metal-backed framebuffer. The Python
control plane talks to a thin sidecar over a typed local RPC (keeps Python clean). `vz` becomes the
default macOS-local provisioner; QEMU macOS (Phase 08 stop-gap) remains a fallback flag.

**Tests:** `test_vz_provision_refused_on_non_apple`, `test_vz_sidecar_rpc_contract` (mock sidecar).

**Do not:** attempt `vz` on Intel/Linux hosts; remain hard-refused off Apple hardware.

---

## Task 09-12: macOS MediaSource + InputSink (SCK/VideoToolbox)

**Files:** `apps/api/app/adapters/macos/stream_local.py` (new), `adapters/macos/input.py` (new).

Capture via **ScreenCaptureKit** (filtered to the VM display), encode via **VideoToolbox**
(`vtenc_h264`, hardware) → `encoded_track`. Inject input via the `vz` virtual HID (or CGEvent in the
sidecar). Replaces `screencapture -x` for the **live** path; MCP one-shot screenshot may still use
the simple path.

**Tests:** `test_macos_source_uses_screencapturekit` (mock), `test_macos_input_via_vz_hid`.

**Do not:** use `screencapture` polling for the live stream.

---

## Task 09-13: iOS-sim MediaSource + InputSink

**Files:** `apps/api/app/adapters/ios_sim/stream_local.py` (new), `adapters/ios_sim/input.py` (new).

Capture the **Simulator window** via ScreenCaptureKit (window filter) → VideoToolbox →
`encoded_track`. Input via a persistent `simctl`/SimulatorKit HID path (not per-event `osascript`,
which is slow). Apple-gated.

**Tests:** `test_ios_sim_source_filters_simulator_window` (mock), `test_ios_sim_input_persistent`.

**Do not:** use `simctl io screenshot` polling for the live stream.

---

## Task 09-14: Attach / Detach interactive session

**Files:** `apps/api/app/api/routes/stream.py` (extend), `services/device_session.py` (new).

Implement the runtime **display_mode** toggle (D-1): `POST /devices/{id}/display/attach` starts a
`MediaSource` + negotiable peer and sets `display_mode=interactive`; `POST …/display/detach` tears
down the stream and sets `display_mode=headless` **without reprovisioning**. MCP exposure is
unaffected (orthogonal axis). Emits audit + log-bus events.

**Tests:** `test_attach_sets_interactive_and_starts_source`, `test_detach_returns_to_headless`,
`test_attach_does_not_reprovision`.

**Do not:** couple attach to MCP on/off — they are independent toggles.

---

## Task 09-15: Display & quality profiles

**Files:** `apps/api/app/stream/profiles.py` (new); used by pipelines/sources.

Profiles: `smooth` (30–60fps, motion) vs `sharp_text` (10–15fps, higher per-frame quality for
read-heavy agent work). **Freeze-drop**: when frames are static, drop to ~1fps to save CPU/bandwidth
and snap back on motion. Local pins high CBR (bandwidth is free); cloud uses capped CRF + transport-cc
ABR via `set_bitrate`. Per-device override stored on the device/session.

**Tests:** `test_profile_sharp_text_lowers_fps_raises_quality`, `test_freeze_drop_reduces_fps_when_static`.

**Do not:** apply ABR on local (no-op there).

---

## Task 09-16: Audio track — device audio → Opus → browser

**Files:** `apps/api/app/stream/audio_source.py` (new); edit `stream/peer.py` to add an audio
track alongside the video track; edit per-family sources to wire audio.

Add a second WebRTC track (audio, Opus) to every `StreamPeer`. Per-family capture:

| Family | Audio capture |
|--------|--------------|
| Linux (Docker) | PulseAudio/ALSA virtual sink → GStreamer `pulsesrc`/`alsasrc` → Opus |
| Android | scrcpy-server already streams audio in its protocol (enable the audio channel) |
| Windows (QEMU) | QEMU `-audiodev pa,id=snd0 -device ich9-intel-hda` → VirtIO audio → host PulseAudio/PipeWire → GStreamer → Opus |
| macOS (`vz`) | `vz` VZVirtioSoundDeviceConfiguration → host CoreAudio → AVFoundation/AVAudioEngine → Opus |
| iOS-sim | ScreenCaptureKit audio stream → AVAudioEngine → Opus |

Audio is a required part of `display_mode=interactive` — attaching a session always starts both
tracks. `AudioSource` follows the same `start/stop` lifecycle as `MediaSource`; the SPI factory
(09-01) resolves `audio_source_for(device)` by `(family, location)`.

**Tests:** `test_peer_adds_audio_track`, `test_audio_source_factory_dispatches_by_family`,
`test_attach_starts_audio_and_video_tracks`.

**Do not:** offer audio as an optional toggle — it is always on in interactive mode.

---

## Task 09-17: Stream log-bus events + latency acceptance harness

**Files:** edit `stream/peer.py`/`gateway.py` to emit; `tests/stream/test_latency_budget.py` (new).

Emit `source=stream` log-bus events: negotiate, ICE state, first-frame, keyframe, bitrate change,
reconnect, teardown. Add an automated **glass-to-glass latency** harness asserting the
`interactive-workspace-plan.md` budgets (local HW < 50ms; local SW < 100ms) using a timestamp-overlay
test pattern decoded on a headless client.

**Tests:** `test_stream_emits_session_events`, `test_local_hw_latency_under_budget` (marked, runs
where HW encode available; soft-skip otherwise).

**Do not:** emit per-frame log spam (session-level events only — D-4).

---

## Task 09-18: Cloud variants (back-loaded, ADR-gated)

**Files:** `docs/design/streaming-cloud-vs-local.md` (new); in-guest agent stubs under
`adapters/*/stream_cloud.py`; `stream/ice.py` coturn branch; `adr-00xx-coturn-cloud-turn.md`.

Document and stub the **capture-locus divergence**: on cloud, AWS owns the hypervisor → capture
**must** be in-guest (Windows Desktop Duplication / macOS ScreenCaptureKit agent / Linux Selkies or
DCV), encode on the EC2 GPU tier, traverse NAT via coturn in the user's VPC. Ship stubs + the ADR;
full cloud implementation is a follow-on once local is proven.

**Tests:** `test_cloud_ice_requires_turn_config`, `test_cloud_source_stub_documents_in_guest_capture`.

**Do not:** block local delivery on cloud streaming; this task is scoping + stubs + ADR only.

---

## Exit criteria

- A **local Android** device streams a real, scrcpy-sourced H.264 video **and audio** into the
  browser via the existing WebRTC signaling, with input injected over the data channel — end to end.
- Linux (Xvfb+GStreamer), Windows (VNC-bridge+QMP), and macOS/iOS-sim (vz+SCK+VideoToolbox) each have
  a working `MediaSource`/`AudioSource`/`InputSink`.
- Every interactive session always has both a video track and an audio track — they are not separable.
- **Attach/Detach** flips a device between headless and interactive with no reprovision; MCP exposure
  is independent.
- aiortc encoded-passthrough works (or the ADR records the documented fallback).
- Local hardware-encode glass-to-glass latency meets the < 50 ms budget in the acceptance harness;
  local ICE is loopback-only with no STUN/TURN.
- Cloud capture-locus divergence is documented + stubbed + ADR'd (not fully built).
