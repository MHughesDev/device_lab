---
doc_id: "ADR-0007"
title: "coturn for WebRTC TURN in cloud deployments (BYOC)"
status: "accepted"
date: "2026-06-01"
deciders: ["mhughesdev"]
---

# ADR-0007: coturn for WebRTC TURN in cloud deployments (BYOC)

## Status

Accepted

## Context

Local DeviceLab sessions use loopback ICE only — both peers are on the same
machine, so STUN/TURN is unnecessary. Cloud device sessions (EC2) require NAT
traversal when the browser is on a different machine from the API server.

DeviceLab's BYOC model requires that all cloud infrastructure, including TURN
servers, lives in **the user's own AWS account**.

## Decision

For cloud device sessions (`location=cloud`):
- Include **STUN** (`stun:stun.l.google.com:19302` as default public STUN)
- Include **TURN** via a user-provisioned **coturn** EC2 instance in the user's VPC

coturn configuration is read from settings:
```
WEBRTC_STUN_URL=stun:stun.example.com:3478
WEBRTC_TURN_URL=turn:turn.example.com:3478
WEBRTC_TURN_USERNAME=user
WEBRTC_TURN_CREDENTIAL=secret
```

For local sessions (`location=local`), the ICE config is **loopback-only**:
no STUN, no TURN, single `127.0.0.1` host candidate. This honors the
localhost-only control plane invariant and reduces connect time to near-zero.

## Consequences

- Users must provision and operate their own coturn EC2 instance (BYOC boundary).
- DeviceLab provides an operations guide for coturn setup in the user's VPC.
- coturn credentials are stored in settings (backed by `keyring`) — never plaintext
  in model context.
- Cloud streaming full implementation is a follow-on to Phase 09 local delivery.
  Phase 09 ships the ICE config split and stubs the cloud path.

## Alternatives considered

- **Twilio TURN / Metered TURN**: third-party TURN violates the BYOC boundary
  (user data traverses a third-party server).
- **AWS Global Accelerator**: more complex; coturn is simpler and well-understood.
