---
doc_id: "23.7"
title: "Research notes — streaming and WebRTC input"
section: "Research"
summary: "Skim notes on DCV, Selkies/Kasm/scrcpy patterns, TURN, codecs, separate input channels."
updated: "2026-05-17"
---

# Notes — Streaming, WebRTC, codecs, input paths

## Layered transport strategy

- **Never rely on SSM alone for high-bandwidth interactive video** — historically throughput-limited for bulk transfers; fine for control/agent APIs [prior round].
- **Primary interactive paths:**
  - **Amazon DCV** where AWS-native desktop streaming fits (Windows/Linux GPU tiers) [S015].
  - **OSS WebRTC desktop** (Selkies lineage / evaluation against KasmVNC experimental WebRTC UDP) for Linux [S016,S017].
  - **Android:** framebuffer → encoder → browser via **WebCodecs/H.264** pipelines inspired by scrcpy/ws-scrcpy community patterns [S018].

## Signaling & NAT

- **STUN** public services acceptable for experiments.
- **TURN (coturn)** deployed into **user’s VPC** for reliable NAT traversal — security groups + TLS on 443 pattern widely documented [Q8].

## Hardware encode

- Offer **G4dn / G6** profiles when realtime encode CPU load hurts emulator performance — NVENC on T4/L4 families per AWS docs [Q9].

## Separate input channel

- Mirror gaming-remote-desktop practice: **WebRTC data channels** — keyboard ordered reliable; high-frequency pointer moves unreliable/low latency [Q10].
- Automation APIs (Playwright/UIA/ADB) remain authoritative over pixel-stream round-trips for AI efficiency.

## Audio

- Phase into templates once desktop parity demanded — multiplex or separate Opus stream; template-flagged.
