---
doc_id: "18.3"
title: "open questions"
section: "Root"
status: "current"
summary: "Initialization-tracked open questions from idea.md with blocking classification and disposition."
updated: "2026-05-17"
---

# Open Questions
<!-- derived from: idea.md §19 -->

This file records unresolved product decisions from `idea.md` and classifies each one by delivery impact. Blocking items are also represented as `category=human-ops` rows in `queue/queue.csv`.

## Classification keys

- `architecture-blocking`: would change foundational boundaries if answered differently.
- `implementation-blocking`: architecture is stable, but execution details are blocked.
- `non-blocking`: can proceed with default assumptions and revisit later.

## Questions

| Q-ID | Question | Classification | Current default | Status |
|---|---|---|---|---|
| OQ-001 | Is Tauri in initial roadmap or post-v1? | non-blocking | Docker Compose + localhost is default v1 install path | Open |
| OQ-002 | Runtime agent language: Go accepted or run Go-vs-Rust spike first? | implementation-blocking | Plan assumes Go; spike row decides final language before deep runtime build-out | Open |
| OQ-003 | Default local general-purpose VLM when enabled: bundled or BYOK-only? | implementation-blocking | BYOK-only escalation path remains default | Open |
| OQ-004 | Browser family: include WebDriver BiDi in v1 or defer? | implementation-blocking | Playwright + CDP is v1 default | Open |
| OQ-005 | Ship warm-pool recommended defaults per template or leave opt-in only? | implementation-blocking | Warm pools off by default | Open |
| OQ-006 | Cross-family recorder fidelity for v1 (beyond browser codegen)? | implementation-blocking | Browser-first recording; mobile/desktop recorder phased later | Open |
| OQ-007 | Vault plugin timing (v1 or v2)? | non-blocking | OS keychain is required baseline; Vault stays optional plugin | Open |
| OQ-008 | OTel exporter default: bundled local stack or user-provided endpoint? | implementation-blocking | User-provided OTLP endpoint default | Open |
| OQ-009 | mTLS cert lifecycle ownership for gateway<->runtime channel? | implementation-blocking | DeviceLab-managed short-lived certs unless user PKI is configured | Open |
| OQ-010 | AWS multi-account support timing (v1 or post-v1)? | implementation-blocking | Single-account v1 with post-v1 AssumeRole chain expansion | Open |
