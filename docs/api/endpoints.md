---
doc_id: "4.1"
title: "endpoints"
section: "API"
summary: "DeviceLab control-plane API and MCP surface derived from initialization spec."
updated: "2026-05-17"
---

# 4.1 — endpoints

<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §7 §12 -->

**Purpose:** Catalog of planned control-plane API endpoints and MCP tool groups for DeviceLab initialization.

## 4.1.1 REST control plane (`/api/v1`)

| Method | Path | Purpose | Auth | Request shape | Response shape |
|---|---|---|---|---|---|
| `GET` | `/workspace` | Return workspace config and health summary | local operator | none | workspace + account + feature flags |
| `POST` | `/cloud-accounts` | Connect AWS account via profile/SSO/assume-role | local operator | credential selector + region | connection status |
| `POST` | `/cloud-accounts/{id}/preflight` | Validate IAM/quota/capacity/bootstrap requirements | local operator | check options | preflight report |
| `GET` | `/templates` | List device templates and capabilities | local operator | family/profile filters | template list |
| `POST` | `/devices` | Create a device from template/profile/region | local operator | template/profile/region + tags | device record |
| `GET` | `/devices` | List devices and lifecycle states | local operator | state/family/region filters | paginated devices |
| `GET` | `/devices/{id}` | Fetch one device details | local operator | none | device detail |
| `GET` | `/devices/{id}/events` | SSE lifecycle and phase updates | local operator | optional since cursor | server-sent events |
| `POST` | `/devices/{id}/lifecycle/{action}` | start/stop/restart/snapshot/terminate | local operator (+confirm on dangerous) | optional options payload | action ticket/result |
| `GET` | `/devices/{id}/stream` | Return stream negotiation metadata | local operator | none | WebRTC signaling payload |
| `POST` | `/devices/{id}/recipes/run` | Execute a recipe with inputs | local operator | recipe id + inputs | run id + status |
| `GET` | `/tests/runs/{id}` | Retrieve run status and summary | local operator | none | test run detail |
| `GET` | `/artifacts` | List artifacts with filters | local operator | run/device/type filters | artifact metadata list |
| `GET` | `/cost/summary` | Show active spend and cap status | local operator | optional scope | cost summary |
| `GET` | `/mcp/config` | Generate MCP client config snippets | local operator | client type | config payload |
| `POST` | `/mcp/clients/{id}/rotate` | Rotate MCP client token | local operator | optional expiry | token metadata |
| `GET` | `/audit` | Read audit event stream | local operator | filters + pagination | audit events |

## 4.1.2 MCP gateway (`/mcp` for Streamable HTTP, stdio supported)

Tool groups exposed by capability handshake:

- `inventory`
- `lifecycle`
- `observe`
- `interact`
- `forms`
- `read_content`
- `recipes`
- `subscribe`
- `files`
- `network`
- `identity`
- `cost_safety`

### MCP action envelope contract

Every action returns:

- `screen_version_before`
- `screen_version_after`
- `observation_delta`
- `evidence_id`
- `warnings[]`

Every observation includes:

- `screen_version`
- `timestamp`
- `observation_tiers` (AX/OCR/vision metadata)

## 4.1.3 Notes

- Endpoint list in this doc is the initialization contract; concrete OpenAPI docs are updated as routes land.
- Dangerous lifecycle and shell-like operations must enforce confirmation and audit logging.
