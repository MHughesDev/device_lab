---
doc_id: "24.3"
title: "Phase 02 — BYOC provisioning MVP"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-05-31"
---

# Phase 02 — BYOC Provisioning MVP

## Objective

Connect to the user's AWS account, explain readiness failures clearly, bootstrap required cloud-side resources, and execute the first full Linux device lifecycle (requested → ready → terminated). Add a browser session baseline. The user should be able to go from clone to a live Linux shell session — mediated by DeviceLab — in a single documented workflow.

---

## OSS pulled in this phase

| Repo / package | What we take | Where it lands |
|----------------|-------------|----------------|
| `boto3` (`pip install boto3`) | AWS SDK — EC2, SSM, IAM, STS, S3, pricing | `apps/api/app/adapters/aws/` |
| `awspricing` (`pip install awspricing`) | Pricing lookup + cache | `apps/api/app/services/cost/pricing.py` |
| `cloud-custodian` (reference only, do not pip install) | `c7n/resources/ec2.py` tagging + lifecycle patterns; `c7n/tags.py` tag enforcement | Ported into `apps/api/app/adapters/aws/ec2.py` and `apps/api/app/adapters/aws/tags.py` |
| `browser-use` (`pip install browser-use`) | `browser_use/browser/` context manager pattern for browser session lifecycle | `apps/api/app/adapters/browser/session.py` |

---

## Implementation tasks

### 1. Cloud account persistence + credential selection

Files: `apps/api/app/services/cloud_account.py`, `apps/api/app/api/routes/cloud_accounts.py`

```
POST /api/v1/cloud-accounts
  body: { provider: "aws", display_name, credential_source: "env"|"profile"|"role", region }
  → CloudAccount with status: "pending_preflight"

GET /api/v1/cloud-accounts
GET /api/v1/cloud-accounts/{id}
DELETE /api/v1/cloud-accounts/{id}
```

Credential sources: `env` (AWS_ACCESS_KEY_ID/SECRET), `profile` (named `~/.aws/credentials` profile), `role` (IAM role ARN for assume-role). Source selection stored in `CloudAccount.credential_source`. Raw credentials never stored — only the source descriptor.

### 2. AWS provider boundary

Files: `apps/api/app/adapters/aws/__init__.py`, `apps/api/app/adapters/aws/client.py`

Create an `AWSClient` class wrapping `boto3.Session`:

```python
class AWSClient:
    def caller_identity(self) -> dict          # sts.get_caller_identity()
    def list_regions(self) -> list[str]        # ec2.describe_regions()
    def check_quota(self, service, quota) -> float  # service-quotas API
    def simulate_policy(self, actions, resources) -> list[PolicyResult]  # iam.simulate_principal_policy()
    def check_ssm_availability(self, region) -> bool
    def describe_ec2_capacity(self, region, instance_type) -> CapacityResult
    def get_on_demand_price(self, region, instance_type) -> Decimal   # via awspricing
```

All methods raise typed `AWSProviderError` subclasses, never raw `botocore.exceptions`.

### 3. Preflight service

Files: `apps/api/app/services/preflight.py`, `apps/api/app/api/routes/cloud_accounts.py`

```
POST /api/v1/cloud-accounts/{id}/preflight
  → PreflightReport {
      status: "pass"|"warn"|"fail",
      checks: [
        { name, status, severity, message, remediation, evidence, retryable }
      ]
    }
```

Checks to implement:
- `caller_identity` — can we auth to AWS at all?
- `required_permissions` — IAM simulate: EC2 run/stop/terminate, SSM send-command, S3 put/get, pricing:GetProducts
- `region_availability` — selected region is available and EC2 is reachable
- `ssm_available` — SSM endpoint accessible in region
- `capacity_check` — t3.micro (default Linux template) has capacity
- `service_quotas` — running instance count below limit

Every failed check includes a `remediation` string the operator can act on immediately.

### 4. Bootstrap planner + executor

Files: `apps/api/app/services/bootstrap.py`

Bootstrap creates the minimum AWS resources DeviceLab needs before any device can provision:
- IAM role `DeviceLab-RuntimeAgent` with SSM + S3 + CloudWatch permissions
- Security group `DeviceLab-Default` (no inbound, SSM egress only)
- S3 bucket `devicelab-artifacts-{account_id}` with lifecycle rules and BYOC tags

Before applying: produce a `BootstrapPlan` listing resources to create, permissions needed, estimated cost impact ($0 for IAM/SG, ~$0.02/GB for S3). Require explicit confirmation before executing. Tag every resource `DeviceLab:Workspace={workspace_id}`.

Bootstrap status stored on `CloudAccount.bootstrap_status` ∈ `{not_started, planning, in_progress, complete, failed}`.

Port the idempotent handler + progress event pattern from `cloudformation-cli-python-plugin` — specifically the `ProgressEvent` model and the "check then create" idempotency approach.

### 5. Linux adapter + runtime agent

Files: `apps/api/app/adapters/linux/adapter.py`, `apps/api/app/adapters/linux/agent_bootstrap.py`

Linux adapter methods:
```python
async def provision(device: Device, template: DeviceTemplate) -> ProviderIds
async def wait_for_running(instance_id: str, timeout: int) -> None
async def bootstrap_agent(instance_id: str) -> None   # SSM send-command
async def wait_for_agent(device_id: str, timeout: int) -> None
async def terminate(device: Device) -> None
async def get_lifecycle_events(instance_id: str) -> list[LifecycleEvent]
```

`bootstrap_agent` uses SSM Run Command to:
1. Install Python 3.12 if not present
2. Download `devicelab-agent` (a small Python script, written in this phase)
3. Start the agent as a systemd service
4. Agent opens an SSM session tunnel back to the control plane

Port EC2 tagging conventions from `cloud-custodian`'s `c7n/tags.py`:
- Every instance gets `DeviceLab:Workspace`, `DeviceLab:Device`, `DeviceLab:Template`, `DeviceLab:ManagedBy=devicelab`
- Orphan detection uses these tags

### 6. Runtime agent (cloud-side, minimal)

Files: `apps/api/app/agent/` (this is the code that runs on the EC2 instance)

Seed from the STF (`openstf/stf`) hub/provider/agent split concept:
- Hub = DeviceLab control API
- Provider = the EC2 instance + its resources
- Agent = lightweight Python process running on the instance

Phase 02 runtime agent only needs to:
- Send heartbeat pings to control API via SSM session tunnel
- Report that it is alive and ready (`agent_ready` FSM trigger)
- Accept a `terminate` signal and shut down cleanly

Write from scratch (~150 lines). STF is the architecture reference, not code to copy.

### 7. Browser adapter baseline

Files: `apps/api/app/adapters/browser/adapter.py`, `apps/api/app/adapters/browser/session.py`

Port the browser session lifecycle pattern from `browser-use/browser_use/browser/context.py`:
- `BrowserSession.create()` → launch Chromium via Playwright, return session
- `BrowserSession.close()` → clean shutdown with artifact capture
- `BrowserSession.navigate(url)` → navigation with wait
- Session has its own `Device` record in the FSM (provisioning → ready on launch success)

Browser sessions run locally in phase 02 (no cloud EC2 yet for browsers). Cloud browser via remote Chromium / EC2 is phase 06.

Capability declaration for browser: `{ observe: ["ax_tree", "screenshot"], interact: ["click", "type", "navigate", "fill_form"], streaming: false }`.

### 8. Device templates catalog + provisioning API

Files: `apps/api/app/services/templates.py`, `apps/api/app/api/routes/templates.py`, `apps/api/app/api/routes/devices.py`

```
GET /api/v1/templates
  → [{ id, family, name, description, capability_json, supported_regions }]

POST /api/v1/devices
  body: { template_id, cloud_account_id, region }
  → Device { id, state: "requested", ... }
  (async — FSM transitions happen in background task)

GET /api/v1/devices/{id}
GET /api/v1/devices/{id}/events
POST /api/v1/devices/{id}/lifecycle/stop
POST /api/v1/devices/{id}/lifecycle/start
POST /api/v1/devices/{id}/lifecycle/terminate
```

Seed templates:
- `linux-default`: t3.medium, Ubuntu 24.04, SSM-enabled AMI, all supported regions
- `browser-local`: local Chromium, no cloud account required, no region

### 9. First-run wizard UI

Files: `apps/web/src/routes/_layout/onboarding.tsx`, `apps/web/src/components/Onboarding/`

Multi-step wizard:
1. **Connect account** — credential source picker, region selector
2. **Preflight** — live check list showing pass/warn/fail with remediation text
3. **Bootstrap** — show plan, confirm button, progress stream
4. **First device** — template picker, provision button, live state badge
5. **Done** — MCP config copy snippet + link to docs

---

## Exit criteria

- User can connect an AWS account, run preflight, see clear pass/fail per check.
- Bootstrap creates the three required resources idempotently.
- A Linux device can reach `ready` state end-to-end in integration tests (with fake AWS adapter).
- A browser session can reach `ready` state and be terminated cleanly.
- `terminate` path is covered with cleanup verification (no orphaned resources per tags).
- Cost estimate appears on every `Device` record at provisioning time.
- First-run wizard navigates all 5 steps without errors on a happy path.
