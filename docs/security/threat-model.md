---
doc_id: "16.8"
title: "threat model"
section: "Security"
status: "current"
summary: "DeviceLab threat model covering local control plane, MCP abuse paths, and BYOC cloud safety boundaries."
updated: "2026-05-17"
---

# Threat Model
<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §14 §18 -->

## System boundary

- Local-first control plane on user machine.
- Cloud-side execution in user-owned AWS account.
- AI clients connect through MCP with scoped permissions.

## Top threats and mitigations

| Threat | Attack path | Mitigations |
|---|---|---|
| Unauthorized MCP tool execution | leaked token or over-permissive client scope | per-client token rotation, scoped tool groups, dangerous mode disabled by default, confirmation gates |
| Secret exfiltration into model context | tool responses/logging include plaintext secrets | Identity Broker secret refs only, no secret return values, output redaction pipeline, audited secret inject path |
| Cloud resource abuse / cost runaway | malicious or mistaken automation provisions expensive resources | hard/soft cost caps, dangerous-operation confirmations, explicit Mac/GPU warning gates, orphan sweeper |
| Prompt-injection-driven unsafe actions | web/app content manipulates AI to issue unsafe calls | trusted-tool policy, confirmation for dangerous actions, defensive prompt-injection filtering and scoped permissions |
| Public exposure of runtime surfaces | accidental open ports to device endpoints | localhost-first defaults, SSM tunnels, user-owned TURN, no public inbound ports by default |
| Replay/evidence tampering | attacker modifies forensic trails | append-only audit events, checksummed evidence payload references, immutable timestamps |

## Accepted risks

- User-operated environments can still misconfigure local machine/network controls.
- Optional VLM integrations can increase data egress risk when enabled by user BYOK settings.
- BYOC means IAM misconfiguration in user accounts can impair safety guarantees.

## Security priorities

1. Preserve secret non-disclosure to AI context.
2. Enforce capability-based authorization and confirmation gates.
3. Keep cloud operations tagged and auditable.
4. Fail closed on tunnel/runtime-agent trust failures.
