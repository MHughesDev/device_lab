---
doc_id: "ADR-0005"
title: "scrcpy-server for Android screen streaming and control"
status: "accepted"
date: "2026-06-01"
deciders: ["mhughesdev"]
---

# ADR-0005: scrcpy-server for Android screen streaming and control

## Status

Accepted

## Context

Android devices need real-time screen streaming and input injection. Options:
- `adb screenrecord` — 1–2s buffer, 180s cap, no interactive control
- `uiautomator2` screenshot loop — too slow for interactive (~1fps)
- **scrcpy-server.jar** — device-GPU MediaCodec H.264, sub-frame latency control

## Decision

Use **scrcpy-server** running on the Android device via `adb shell` to:
1. Encode the display with **MediaCodec** (device GPU) — no host re-encode
2. Stream raw H.264 access units over an adb-forwarded TCP socket
3. Accept input via the **scrcpy control socket** (binary protocol, sub-frame)

The H.264 bitstream is fed directly into `EncodedVideoTrack.push_au()` (no re-encode).
Input events are encoded per the scrcpy `ControlMsg.java` protocol.

scrcpy-server.jar is vendored at `adapters/android/vendor/scrcpy-server.jar`.

## Consequences

- `adb` must be in `$PATH` on the host; the adb server must be running.
- scrcpy-server.jar is v2.3; vendored to avoid network deps at runtime.
- The control socket uses a binary wire protocol that must be kept in sync
  with the vendored server version.
- Audio requires `audio=true` flag in the server command (Phase 09-16).
- Fallback to `adb shell input` is retained for degraded mode only.

## Alternatives considered

- **uiautomator2** screenshot + input: suitable for MCP one-shot actions, not
  for interactive streaming (< 2fps screenshot path).
- **ADB screenrecord**: no interactive control path; buffer and cap make it
  unsuitable for WebRTC streaming.
