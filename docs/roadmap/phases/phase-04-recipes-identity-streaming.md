---
doc_id: "24.5"
title: "Phase 04 - Recipes, identity, and streaming"
section: "Roadmap"
status: "current"
completion: "0%"
summary: "Detailed implementation plan for recipe execution, recording, Identity Broker secret references, MCP elicitation, and split stream/input sessions."
updated: "2026-05-30"
---

# Phase 04 - Recipes, Identity, and Streaming
<!-- derived from: queue/queue.csv Q-109 Q-110 Q-111, docs/security/threat-model.md, docs/testing/strategy.md -->

## Objective

Turn one-off interactions into repeatable workflows, allow safe secret use without exposing secret values to agents, and provide a low-latency human session path with split media and input channels.

## Scope

In scope:

- Recipe YAML contract and validation.
- Recipe execution service using phase 03 action primitives.
- Initial recording path that can produce editable recipe artifacts.
- Identity Broker with secret references backed by OS keychain or equivalent local backend.
- MCP elicitation gates for secret use.
- Stream negotiation and separate input data channel contract.
- Session reconnect and telemetry for input latency.

Out of scope:

- Marketplace of recipes.
- Cloud-hosted secret vault by default.
- Perfect recording fidelity across all future families.
- Production TURN hosting beyond BYOC/user-owned deployment guidance.

## Implementation Sequence

1. Define recipe schema.
   Include metadata, supported families, inputs, setup steps, action steps, wait conditions, assertions, artifact captures, cleanup, and safety requirements.

2. Build recipe validator.
   Validate YAML shape, required inputs, capability requirements, dangerous steps, secret references, and target family compatibility before execution.

3. Implement runner.
   Execute recipes through the same observation/action services used by MCP tools. Persist run status, step output, timing, warnings, and artifact references.

4. Add initial recording.
   Capture action envelopes and observation deltas from a session and transform them into a draft recipe. Mark unstable selectors and coordinate fallbacks as warnings.

5. Implement Identity Broker.
   Store `SecretRef` metadata locally while raw values remain in OS keychain or configured backend. Return only references and redacted labels to API/MCP.

6. Add elicitation-gated injection.
   MCP secret use requires an explicit broker flow: request, human or policy approval, scoped injection, audit event, and no raw value in response.

7. Implement stream gateway contract.
   Separate media stream negotiation from input commands. Preserve the semantic action path as the preferred automation route.

8. Add reconnect handling.
   Support reconnect tokens or resumable session identifiers so transient network loss does not orphan device state.

## Recipe Contract Sketch

```yaml
name: login-smoke
version: 1
families: [browser, linux]
inputs:
  base_url:
    type: string
steps:
  - observe:
      tier: structured
  - interact:
      action: fill_form
      target: login
      values:
        username: secret://workspace/demo-user
  - assert:
      text_contains: Dashboard
cleanup:
  - capture_artifacts: [screenshot, logs]
```

## Security Requirements

- Secret values never appear in API responses, MCP payloads, logs, recipe files, or evidence records.
- Every injection records actor, device, recipe/session, secret ref, scope, approval mode, and timestamp.
- Dangerous recipe steps require explicit policy declarations and confirmation handling.
- Stream/input endpoints must require local auth or scoped session tokens.

## Testing and Verification

- Validate recipe schema success and failure cases.
- Test recipe runner idempotency for retryable failed steps.
- Test that raw secrets are absent from serialized payloads and logs.
- Test stream negotiation separately from input commands.
- Test reconnect preserves session continuity and does not duplicate actions.

## Exit Criteria

- A recipe can run against a supported session and produce a persisted run record.
- A recorded session can produce an editable draft recipe with warnings.
- Secret references can be used without exposing raw values.
- Human stream and input paths work without replacing semantic automation contracts.

