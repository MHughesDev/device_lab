---
doc_id: "24.3"
title: "Phase 02 - BYOC provisioning MVP"
section: "Roadmap"
status: "current"
completion: "0%"
summary: "Detailed implementation plan for AWS account connection, preflight, bootstrap, and first Linux/browser device lifecycle slices."
updated: "2026-05-30"
---

# Phase 02 - BYOC Provisioning MVP
<!-- derived from: queue/queue.csv Q-102 Q-103 Q-104 Q-105, docs/architecture/bounded-contexts.md, docs/api/endpoints.md -->

## Objective

Prove that DeviceLab can connect to a user's AWS account, explain readiness failures, bootstrap the required cloud-side pieces, and create the first executable device sessions for Linux and browser families.

## Scope

In scope:

- AWS credential selection and account identity checks.
- Region, quota, IAM, SSM, networking, image, and tagging preflight.
- Bootstrap status model for required IAM roles, security groups, buckets, or runtime artifacts.
- Linux lifecycle state machine from requested to ready to terminated.
- Browser family baseline using Playwright-backed runtime behavior.
- First-run wizard UI path through account connect, preflight, bootstrap, and first session.

Out of scope:

- Android, Windows, macOS, iOS Simulator, and real iOS.
- Warm pools beyond schema and explicit "not enabled" policy.
- Advanced snapshot/fork support.
- Full cost enforcement beyond tagging and estimate placeholders.

## Implementation Sequence

1. Model cloud account connection.
   Add `CloudAccount` persistence with provider, account id, region set, credential source, status, last preflight result, and redacted display metadata.

2. Build AWS provider boundary.
   Create an interface for caller identity, quota lookup, IAM simulation or policy checks, SSM availability, EC2 capacity checks, pricing lookup hooks, and bootstrap deployment operations.

3. Implement preflight report contract.
   Return structured checks with `status`, `severity`, `message`, `remediation`, `evidence`, and `retryable`. Every failure should tell the operator what to fix.

4. Add bootstrap planner.
   Produce a plan before applying changes. The plan should list resources, permissions, estimated cost impact, and cleanup tags.

5. Implement lifecycle state machine.
   Define device states such as `requested`, `preflight_blocked`, `provisioning`, `bootstrapping_agent`, `ready`, `stopping`, `stopped`, `terminating`, `terminated`, and `failed`.

6. Ship Linux vertical slice.
   Provision the simplest Linux template, install or start the runtime agent, report lifecycle events, and support terminate cleanup.

7. Ship browser baseline.
   Add browser template catalog entry and Playwright-backed session behavior. Browser capability declarations should differ from Linux rather than reusing a generic blob.

8. Connect first-run wizard.
   UI should walk through credentials, region, preflight, bootstrap, first device, and MCP config copy/status.

## Data and Service Details

| Entity | Required fields for this phase |
|---|---|
| `CloudAccount` | provider, account id, display name, credential source, default region, status, last checked, preflight summary. |
| `DeviceTemplate` | family, image/source, supported regions, minimum resources, capability declaration. |
| `Device` | template id, family, region, state, phase, provider ids, tags, created by, cost estimate reference. |
| `AuditEvent` | actor, action, target, decision, timestamp, redacted metadata. |

## API Contracts

- `POST /api/v1/cloud-accounts`
- `POST /api/v1/cloud-accounts/{id}/preflight`
- `GET /api/v1/templates`
- `POST /api/v1/devices`
- `GET /api/v1/devices/{id}`
- `GET /api/v1/devices/{id}/events`
- `POST /api/v1/devices/{id}/lifecycle/terminate`

## Testing and Verification

- Unit test preflight result classification.
- Use fake AWS adapters for lifecycle tests.
- Add contract tests for preflight remediation payloads.
- Add cleanup tests that verify provider resource ids and tags are tracked.
- Smoke test first-run wizard with fake account/preflight success.

## Exit Criteria

- A user can connect an AWS account path and see useful preflight output.
- Linux and browser templates appear in the catalog with distinct capabilities.
- A Linux device can reach `ready` through the service contract in tests.
- Termination cleanup path is covered before any wider family expansion.

