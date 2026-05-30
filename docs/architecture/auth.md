---
doc_id: "2.13"
title: "authentication and authorization"
section: "Architecture"
status: "current"
summary: "DeviceLab local auth model, MCP client authorization, and dangerous-action confirmation policy."
updated: "2026-05-17"
---

# Authentication and Authorization
<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §10 §11 §12 §14 -->

## Strategy summary

- DeviceLab has no SaaS account system and no public sign-up.
- Local UI is single-operator by default, optionally guarded by workspace unlock.
- AWS identity is delegated via user profile/SSO/AssumeRole; DeviceLab never stores root keys.
- MCP clients authenticate separately using per-client tokens and scoped permissions.

## Auth surfaces

| Surface | Principal | Mechanism |
|---|---|---|
| Local web UI/API | local operator | loopback-only session (no internet exposure) |
| AWS cloud APIs | user-owned cloud account | AWS SDK credentials from profile / SSO / AssumeRole |
| MCP gateway | AI clients | bearer token + MCP session headers (`MCP-Session-Id`, protocol version) |
| Gateway-to-runtime channel | internal services | mTLS over SSM tunnel |

## Authorization model

MCP permissions are capability-oriented and lease-scoped:

- `Observe`: read inventory, observations, events.
- `Interact`: click/type/semantic actions.
- `Test`: run recipes and test suites.
- `Manage`: lifecycle operations and snapshots.
- `Admin`: client/token/config management.
- `Dangerous`: shell/delete/terminate/cost-cap overrides (off by default).

Each client also has:

- `read_scope` (which devices/resources can be read),
- `write_scope` (which actions are allowed),
- `cost_tier` (maximum spend envelope for operations).

## Confirmation and elicitation policy

- Dangerous operations require explicit confirmation through MCP elicitation.
- Secret-entry flows use elicitation URL mode where sensitive value handling is needed.
- All dangerous-tool calls emit immutable `AuditEvent` entries.

## Access matrix (control plane)

| Endpoint group | Local operator | MCP Observe | MCP Interact | MCP Manage/Admin |
|---|---:|---:|---:|---:|
| `/api/v1/workspace`, `/api/v1/templates` | allow | deny | deny | deny |
| `/api/v1/cloud-accounts*` | allow | deny | deny | deny |
| `/api/v1/devices` read/list | allow | allow (tool mediated) | allow (tool mediated) | allow |
| `/api/v1/devices` lifecycle actions | allow | deny | limited | allow + confirm |
| `/api/v1/mcp/*` client admin | allow | deny | deny | admin only |
| MCP `observe.*` tools | n/a | allow | allow | allow |
| MCP `interact.*` / `forms.*` | n/a | deny | allow | allow |
| MCP `cost_safety.*`, `identity.*`, destructive ops | n/a | deny | deny unless granted | allow + confirmation |

## Multi-tenancy note

Per current product constraints this system is single-workspace, not SaaS multi-tenant. If multi-workspace mode is introduced later, this document must be revised with isolation guarantees and boundary enforcement.
