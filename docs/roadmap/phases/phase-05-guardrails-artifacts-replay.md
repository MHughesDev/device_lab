---
doc_id: "24.6"
title: "Phase 05 — Guardrails, artifacts, and replay"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-05-31"
---

# Phase 05 — Guardrails, Artifacts, and Replay

**Progress: 0%** `░░░░░░░░░░` — not started

## Objective

Close the safety and accountability loop before broadening device family coverage. Every expensive lifecycle action passes through cost policy. Every test run produces retrievable artifacts. Every MCP action is replayable with full before/after evidence. This phase makes the system defensible — if something goes wrong, you can explain exactly what happened and why.

---

## OSS pulled in this phase

| Repo / package | What we take | Where it lands |
|----------------|-------------|----------------|
| `awspricing` (already in) | Real-time pricing lookups for cost estimate accuracy | `apps/api/app/services/cost/guardrail.py` |
| `mitmproxy` (`pip install mitmproxy`) | Embeddable intercepting proxy + custom addon for network capture | `apps/api/app/adapters/network/proxy.py` |
| `cloud-custodian` (reference only) | Orphan detection + tag-based resource inventory patterns from `c7n/resources/ec2.py` | Ported into `apps/api/app/services/cost/inventory.py` |
| `lulzasaur9192/agent-audit-log-examples` (already in from phase 01) | HMAC chain is now the authoritative evidence integrity mechanism | Extended in `apps/api/app/core/audit_log.py` |

---

## Implementation tasks

### 1. Cost policy model

Files: `apps/api/app/services/cost/policy.py`, `apps/api/app/models.py`

```python
class CostPolicy(SQLModel, table=True):
    id: str
    workspace_id: str
    scope: Literal["workspace", "device", "template", "family"]
    scope_id: str | None             # device_id, template_id, or family name
    soft_cap_usd: Decimal | None     # warn at this threshold
    hard_cap_usd: Decimal | None     # block above this threshold
    monthly_budget_usd: Decimal | None
    action_cost_class_overrides: dict # {"snapshot": "expensive", "terminate": "free"}
    override_requires_dangerous_mode: bool
    created_at: datetime
    updated_at: datetime
```

Cost action classes: `free`, `cheap` (<$0.10), `moderate` ($0.10–$5), `expensive` (>$5), `unknown`. Every device action has a declared cost class. Unknown always triggers at least a soft warning.

### 2. Lifecycle guard checks

Files: `apps/api/app/services/cost/guardrail.py`

Before any of these actions: `provision`, `start`, `snapshot`, `fork`, recipe execution with `duration_class=long`:

```python
class CostGuardrail:
    def check(
        action: str,
        device: Device,
        estimated_cost: Decimal,
        workspace_id: str,
    ) -> GuardrailResult:
        ...

class GuardrailResult(BaseModel):
    decision: Literal["allow", "warn", "block"]
    message: str                  # human-readable explanation
    current_spend_usd: Decimal
    soft_cap_usd: Decimal | None
    hard_cap_usd: Decimal | None
    override_available: bool      # true if dangerous_mode can unblock
    evidence_id: str
```

Guardrail decisions are always persisted as `AuditEvent` entries — including `allow` decisions for expensive actions.

### 3. Active resource inventory + orphan detection

Files: `apps/api/app/services/cost/inventory.py`

Port the tag-based resource listing pattern from `cloud-custodian`'s `c7n/resources/ec2.py`:
- `list_tagged_resources(workspace_id)` — describe all EC2 instances tagged `DeviceLab:Workspace={id}`
- Compare with `Device` table records — anything in AWS but not in DB = orphan candidate
- Orphan suggestions returned via `GET /api/v1/cost/orphans`
- Cleanup requires explicit `POST /api/v1/cost/orphans/{resource_id}/cleanup` + dangerous mode check

Pricing cache:
```python
class PricingCache:
    """Wraps awspricing. Refreshes every 24h. Serializes to DB for offline use."""
    def get_ec2_price(region, instance_type, os) -> Decimal
    def get_snapshot_price(region, size_gb) -> Decimal
    def get_data_transfer_price(region) -> Decimal
```

### 4. Snapshot manager

Files: `apps/api/app/services/snapshots.py`, `apps/api/app/adapters/linux/snapshots.py`

```
POST /api/v1/devices/{id}/snapshot
  → Snapshot { id, status: "pending", source_device_id, ... }
  (async — EBS CreateSnapshot, tracks progress via DescribeSnapshots)

GET /api/v1/snapshots/{id}
  → Snapshot { status: "complete"|"pending"|"failed", provider_id, size_gb, cost_estimate }

POST /api/v1/snapshots/{id}/fork
  body: { workspace_id, template_overrides }
  → Device { id, state: "provisioning", forked_from_snapshot_id }

DELETE /api/v1/snapshots/{id}
  (requires dangerous_mode for snapshots older than 24h)
```

Unsupported families return `{ error: "CAPABILITY_UNSUPPORTED", capability: "snapshot" }`. No silent no-ops.

### 5. Network proxy + capture

Files: `apps/api/app/adapters/network/proxy.py`

Embed `mitmproxy` as a library (not subprocess) using `mitmproxy.options.Options` and `mitmproxy.tools.dump.DumpMaster`. Write a custom `mitmproxy` addon:

```python
class DeviceLabAddon:
    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        # Tag flow with device_id, session_id
        # Check against network policy (allowlist/blocklist)
        # Emit evidence event if request matches capture filter

    def response(self, flow: mitmproxy.http.HTTPFlow) -> None:
        # Store captured flow as artifact if enabled
        # Inject headers/responses if recipe step requests it
```

Network proxy is opt-in per device session. Enabling it via MCP/API requires `Manage` role. Starting it for a dangerous action (e.g., credential injection test) requires `Dangerous` role.

### 6. Test run service

Files: `apps/api/app/services/test_runs.py`, `apps/api/app/api/routes/test_runs.py`

```
POST /api/v1/test-runs
  body: { device_id, recipe_id | suite_yaml, collect_artifacts: bool }
  → TestRun { id, status: "running", ... }

GET /api/v1/test-runs/{id}
  → TestRun { status, steps: [{id, status, duration_ms, artifact_refs}], summary }

GET /api/v1/test-runs/{id}/artifacts
  → [Artifact]

GET /api/v1/test-runs/{id}/junit
  → JUnit XML
```

JUnit XML output format:
```xml
<testsuite name="{recipe_name}" tests="{n}" failures="{f}" time="{total_s}">
  <testcase name="{step_id}" time="{step_s}">
    <failure message="{error}" type="{error_code}" />  <!-- if failed -->
  </testcase>
</testsuite>
```

Also emit Allure-compatible metadata (JSON sidecar) for teams using Allure reporting.

### 7. Artifact store

Files: `apps/api/app/services/artifacts.py`

```python
class Artifact(SQLModel, table=True):
    id: str
    workspace_id: str
    session_id: str | None
    run_id: str | None
    evidence_id: str | None
    artifact_type: str   # screenshot, log, video, junit, trace, har, recipe_draft
    storage_path: str    # s3://devicelab-artifacts-{account_id}/...
    size_bytes: int
    content_type: str
    captured_at: datetime
    retention_days: int  # default 30
    purge_after: datetime
```

Retention: 30 days default, configurable per workspace. Purge job runs nightly — marks `purged: true`, does not delete the row (append-only ledger). S3 lifecycle rule handles actual object deletion.

Upload: runtime agent → S3 directly (presigned PUT URL from control API). Download: control API generates presigned GET URL valid for 1 hour.

### 8. Evidence completeness + replay timeline

Files: `apps/api/app/services/replay.py`, `apps/api/app/api/routes/replay.py`

By this phase, every MCP action has an `Evidence` record (from phase 03). Now wire full replay:

```
GET /api/v1/sessions/{id}/timeline
  → [TimelineEvent { timestamp, type, evidence_id, tool, params_summary,
                     before_version, after_version, artifact_refs }]

GET /api/v1/evidence/{id}
  → Evidence + observation_before + observation_after + artifact_refs

POST /api/v1/evidence/{id}/replay
  → RecipeRun (replays the evidence as a recipe step against a new or same device)
```

Replay is not automatic re-execution — it generates a recipe draft from the evidence record and presents it for human review. One-click replay requires explicit confirmation.

HMAC chain integrity check endpoint:
```
GET /api/v1/audit/verify
  → { valid: bool, chain_length: int, first_broken_at: str | null }
```

---

## Cost policy behavior matrix

| Scenario | Decision |
|----------|----------|
| Below soft cap | Allow, no warning |
| At or above soft cap | Allow + visible warning + audit event |
| At or above hard cap | Block + explanation + override path |
| Cost unknown | Conservative warn by default |
| Override requested | Requires `DANGEROUS_MODE=true` + explicit confirm |
| Orphan cleanup | Never automatic — always human-confirmed |

---

## Exit criteria

- Provisioning a device above the hard cap is blocked with a clear error and remediation.
- Soft cap warning appears in API response, MCP response, and UI for devices above threshold.
- Snapshot creates and forks successfully for Linux; returns `CAPABILITY_UNSUPPORTED` for browser.
- Test run produces valid JUnit XML and artifact bundle for a 3-step recipe.
- Artifact retrieval works via presigned S3 URL within retention window.
- Replay timeline orders all evidence records for a session correctly.
- HMAC chain integrity verify endpoint detects a tampered audit event.
- Orphan detection lists untracked tagged resources and cleanup requires explicit confirm.
