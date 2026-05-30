---
doc_id: "23.10"
title: "Research notes — security and observability"
section: "Research"
summary: "Skim notes on keyring headless Linux, mTLS, MCP elicitation, OTel, SBOM, Cursor MCP deeplinks."
updated: "2026-05-17"
---

# Notes — Security, observability, onboarding UX

## Identity Broker + MCP elicitation

- Secrets resolve via OS stores: **Windows/macOS easy via keyring**; **Linux headless** requires **cryptfile/file backend** or dbus-session helper [Q20].
- Sensitive prompts should prefer MCP **elicitation URL mode** per spec (never chat-copy passwords) [S022].

## mTLS on agent gRPC

- Even inside SSM tunnels, use **mTLS + short-lived certs** between gateway and agent for defense-in-depth [Q42,S043].

## Prompt injection via tool outputs

- Implement minimizer/sanitizer firewall pattern at MCP gateway boundary — cite ongoing agent-security literature [Q32].

## Observability

- **OpenTelemetry** instrumentation for FastAPI control plane from day one — traces + metrics; logs via OTLP when enabled [S050,Q31].

## SBOM / supply chain

- Generate **CycloneDX** SBOM on releases; wire GitHub Action provenance when publishing binaries [Q43].

## First-run wizard UX

- Steps: AWS profile validation → region pick → quota preflight → bootstrap stack → download MCP config including **Cursor deeplink** [S044,Q44].
