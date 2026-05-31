---
doc_id: "24.5"
title: "Phase 04 — Recipes, identity, and streaming"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-05-31"
---

# Phase 04 — Recipes, Identity, and Streaming

## Objective

Turn one-off MCP interactions into repeatable, auditable workflows (recipes). Allow safe secret injection without exposing values to agents or logs. Provide a low-latency human session view via WebRTC with a separate input data channel. All three land in the same phase because they are interdependent: recipes inject secrets, streaming requires session tokens, reconnect requires both.

---

## OSS pulled in this phase

| Repo / package | What we take | Where it lands |
|----------------|-------------|----------------|
| `pypyr` (`pip install pypyr`) | Step executor engine; DeviceLab writes custom step modules on top | `apps/api/app/services/recipes/runner.py` |
| `keyring` (`pip install keyring`) | OS keychain backend for SecretRef storage; platform-native on Mac/Linux/Windows | `apps/api/app/services/identity/broker.py` |
| `aiortc` (`pip install aiortc`) | WebRTC peer + data channel; `examples/datachannel-cli` is the seed for split input channel | `apps/api/app/stream/gateway.py` |

---

## Implementation tasks

### 1. Recipe schema + validator

Files: `apps/api/app/services/recipes/schema.py`, `apps/api/app/services/recipes/validator.py`

```yaml
# Example recipe YAML
name: login-smoke
version: 1
families: [browser, linux]
min_devicelab_version: "0.2.0"
inputs:
  base_url:
    type: string
    required: true
  credentials:
    type: secret_ref
    ref: "workspace/demo-creds"
steps:
  - id: open
    action: navigate
    params: { url: "{{ inputs.base_url }}/login" }
  - id: fill
    action: fill_form
    params:
      target: login
      values:
        username: "{{ credentials.username }}"
        password: "{{ credentials.password }}"
  - id: assert_dashboard
    action: wait_for
    params: { condition: "text_contains:Dashboard", timeout_ms: 5000 }
artifacts:
  - capture_screenshot: after_each_step
  - capture_logs: on_failure
cleanup:
  - action: navigate
    params: { url: "about:blank" }
```

Validator checks: YAML schema, required inputs present, capability requirements met by template, secret refs resolve (don't fetch values), dangerous steps declared, family compatibility.

### 2. Recipe runner

Files: `apps/api/app/services/recipes/runner.py`

Use `pypyr` as the step execution engine. Write DeviceLab-specific `pypyr` step modules that wrap the phase 03 interaction service:

```python
# apps/api/app/services/recipes/steps/interact.py
class InteractStep:
    """pypyr step module — executes a DeviceLab interact action."""
    def run_step(context):
        action = context["action"]
        params = context["params"]
        result = interaction_service.execute(action, **params)
        context["last_result"] = result
        if not result.success:
            raise StepError(result.error)
```

Runner persists a `RecipeRun` entity with per-step status, timing, evidence_ids, artifact_refs, and final outcome. Runs are resumable: a failed step can retry from that step without rerunning earlier steps.

### 3. Recipe recording

Files: `apps/api/app/services/recipes/recorder.py`

During a session, record all `ActionResult` envelopes. On recording end:
1. Transform action sequence into recipe YAML draft.
2. Mark steps with coordinate-only targets as `# WARNING: unstable selector`.
3. Suggest `wait_for` steps where action timing was variable.
4. Return draft YAML for human review before saving.

This produces imperfect but useful starting points. Recording is not expected to produce production-ready recipes without human editing.

### 4. Identity Broker + SecretRef

Files: `apps/api/app/services/identity/broker.py`, `apps/api/app/services/identity/models.py`

```python
class SecretRef(SQLModel, table=True):
    id: str                    # uuid
    workspace_id: str
    name: str                  # e.g. "workspace/demo-creds"
    description: str
    backend: str               # "keyring" | "env" (phase 04) | "vault" (future)
    keyring_service: str       # keyring service name
    keyring_username: str      # keyring key within service
    created_at: datetime
    last_used_at: datetime | None
```

`keyring` stores the actual secret value in OS keychain keyed by `(keyring_service, keyring_username)`. The `SecretRef` table stores only metadata — never the secret value.

```python
class IdentityBroker:
    def store(name: str, value: str, description: str) -> SecretRef
    def resolve(ref_name: str, scope: InjectionScope) -> str   # raw value, never logged
    def list_refs(workspace_id: str) -> list[SecretRef]        # metadata only
    def delete(ref_name: str) -> None
```

API:
```
GET  /api/v1/secrets           → [SecretRef] — metadata only, no values
POST /api/v1/secrets           → store new ref
DELETE /api/v1/secrets/{name}
```

### 5. MCP elicitation-gated injection

Files: `apps/api/app/mcp/tools/identity.py`, `apps/api/app/services/identity/elicitation.py`

When a recipe or MCP tool needs a secret:
1. MCP sends an `elicitation` request to the human operator via MCP spec's elicitation mechanism.
2. Human approves (or policy auto-approves for non-dangerous refs in Test+ role sessions).
3. Broker resolves the ref and injects the value into the action payload — value is never in the MCP response.
4. `AuditEvent` is written: `actor=mcp_client_id`, `action=secret_inject`, `target=ref_name`, `scope`, `approval_mode`.

Raw secret values never appear in: API responses, MCP payloads, recipe YAML, evidence records, logs, or screenshots.

### 6. Stream gateway — WebRTC + split input channel

Files: `apps/api/app/stream/gateway.py`, `apps/api/app/stream/peer.py`

Use `aiortc` (`pip install aiortc`). Start from `examples/datachannel-cli` for the split-channel pattern:

```python
# Two channels per session:
# 1. Media track (VideoTrack) — screen capture from runtime agent → client
# 2. Data channel ("input") — keyboard/mouse events from client → runtime agent

class StreamPeer:
    pc: RTCPeerConnection

    async def create_offer(self) -> RTCSessionDescription
    async def set_answer(self, answer: RTCSessionDescription) -> None
    async def add_video_track(self, source: VideoStreamSource) -> None
    async def create_input_channel(self) -> RTCDataChannel
    async def send_input_event(self, event: InputEvent) -> None
    async def close(self) -> None
```

Stream negotiation:
```
POST /api/v1/devices/{id}/stream/negotiate
  body: { sdp_offer, client_id }
  → { sdp_answer, session_token, input_channel_id }
```

The input data channel carries serialized `InputEvent` messages (keyboard, mouse, touch). The media track carries H.264 frames from the runtime agent's screen capture. These are separate so semantic MCP actions remain the preferred automation path — streaming is for human oversight and high-fidelity visual inspection.

Runtime agent stream source: on Linux, use `ffmpeg` piped into an `aiortc` `VideoStreamTrack` subclass. This is the pattern from `aiortc/examples/server/`.

### 7. Session reconnect

Files: `apps/api/app/services/sessions.py`

Each stream session issues a `session_token` (signed JWT, short-lived). On reconnect:
- Client presents `session_token` to `POST /api/v1/devices/{id}/stream/reconnect`.
- Control API verifies token, checks device is still in `ready` state.
- Returns new `sdp_offer` to renegotiate WebRTC — device state is preserved.

Reconnect preserves: current screen version, active recipe run (if any), session evidence history.

### 8. Recipe + stream UI

Files: `apps/web/src/routes/_layout/devices/[id]/stream.tsx`, `apps/web/src/components/Recipes/`

Stream page: WebRTC video element + input event forwarding (keyboard/mouse listeners → data channel). Shows current screen version, live observation badge (AX/OCR/screenshot), active recipe run progress if any.

Recipe UI: YAML editor (Monaco), run button, per-step status timeline, artifact list.

---

## Security invariants (all must have tests)

- Raw secret values never present in any DB column, log line, MCP response, evidence record, or screenshot.
- Every secret injection emits an AuditEvent with actor, ref_name, scope, approval mode.
- Dangerous recipe steps (`raw_shell`, `file_delete`) require `DANGEROUS_MODE=true` + explicit declaration.
- Stream endpoints require valid session_token — not just operator auth.
- Input channel events are rate-limited (anti-spam) and type-validated.

---

## Exit criteria

- A recipe runs against a browser session end-to-end with secret injection and produces a `RecipeRun` with step-level status.
- Secret values are absent from all DB columns, logs, and API responses — verified by test assertions on serialized payloads.
- Recording a 3-step browser session produces a valid draft recipe YAML.
- WebRTC stream negotiates, video renders in browser UI, and input events reach the runtime agent.
- Session reconnect restores stream without losing device state.
- MCP elicitation gate fires for secret-using recipe steps.
