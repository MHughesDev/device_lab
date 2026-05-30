---
doc_id: "24.4"
title: "Phase 03 - MCP observation and interaction"
section: "Roadmap"
status: "current"
completion: "0%"
summary: "Detailed implementation plan for capability-aware MCP tools, structured observation envelopes, screen versioning, semantic actions, and batched steps."
updated: "2026-05-30"
---

# Phase 03 - MCP Observation and Interaction
<!-- derived from: queue/queue.csv Q-106 Q-107 Q-108, docs/api/endpoints.md, docs/architecture/overview.md -->

## Objective

Make DeviceLab useful to AI agents without relying on screenshot loops. Agents should discover only valid tools for the selected device, observe structured state first, execute semantic actions, and batch steps with optimistic screen-version guards.

## Scope

In scope:

- MCP client registration and permission-scoped handshake.
- Tool manifest generation filtered by device family, state, and role.
- Observation envelope with screen version, tier metadata, and deltas.
- Semantic interaction tools for typing, clicking by target, selecting, form filling, waiting, and reading content.
- `run_steps` batching with conflict handling and evidence ids.

Out of scope:

- Full VLM provider integration by default.
- Recipe recording UI.
- Public remote MCP access.
- Secret injection; that lands in phase 04.

## Implementation Sequence

1. Define capability schema.
   Create typed capability declarations for lifecycle, observe, interact, forms, read content, files, network, recipes, identity, and cost safety. Include required permissions and supported families.

2. Build handshake service.
   Given MCP client identity, device id, device family, device state, and permission mode, return protocol version, tool groups, limits, and warnings.

3. Implement observation hub.
   Normalize runtime observations into a common envelope. Use AX/UI tree when available, OCR/text index as secondary, screenshot metadata as fallback, and VLM only when explicitly enabled.

4. Add screen versioning.
   Every observation and action response should include monotonically increasing screen version or equivalent state token. Store enough context to compute deltas.

5. Implement semantic actions.
   Actions should target stable selectors, accessible names, text anchors, coordinates only as fallback, and declared form fields. Each action returns before/after versions and warnings.

6. Add `run_steps`.
   Support a sequence of action and wait steps in one request. Abort on failed guard, unsafe action, timeout, or unexpected screen version. Return partial results.

7. Add subscriptions.
   Provide lifecycle and observation change subscriptions after polling contracts are stable.

## MCP Tool Groups

| Tool group | Phase 03 expectation |
|---|---|
| `inventory` | list templates, devices, capabilities. |
| `observe` | return structured observation tiers and deltas. |
| `interact` | execute target-based semantic actions. |
| `forms` | inspect and fill recognized form fields. |
| `read_content` | extract text, headings, tables, links, and selected regions. |
| `subscribe` | receive lifecycle and observation updates. |
| `cost_safety` | read current guardrail status, even before full enforcement. |

## Error Contracts

| Error | Meaning |
|---|---|
| `DEVICE_NOT_READY` | Tool requires a ready session but lifecycle state is not ready. |
| `CAPABILITY_UNSUPPORTED` | Device family or state does not support the requested tool. |
| `SCREEN_VERSION_CONFLICT` | Expected screen version does not match current version. |
| `TARGET_NOT_FOUND` | Semantic target cannot be resolved. |
| `ACTION_UNSAFE` | Policy or permission check blocked the action. |
| `ACTION_TIMEOUT` | Wait condition or action completion exceeded the configured budget. |

## Testing and Verification

- Contract-test generated MCP manifests for Linux and browser families.
- Unit test observation envelope normalization.
- Test screen-version conflict behavior.
- Test `run_steps` partial failure and rollback/stop semantics.
- Add round-trip-budget tests for common action sequences.

## Exit Criteria

- MCP clients receive filtered tool manifests with no unsupported family actions.
- Structured observation works without screenshot-first behavior.
- Batched semantic actions produce deterministic before/after envelopes.
- UI and MCP paths share service behavior rather than diverging.

