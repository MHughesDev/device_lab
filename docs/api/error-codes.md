---
doc_id: "4.2"
title: "error codes"
section: "API"
summary: "DeviceLab error taxonomy for control plane, MCP safety gates, and cloud integration failures."
updated: "2026-05-17"
---

# 4.2 — error codes

<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §4 §12 §14 -->

**Purpose:** Stable errors for control-plane APIs and MCP tooling.

## 4.2.1 Core errors

| Code | HTTP | Condition | Resolution guidance |
|---|---:|---|---|
| `WORKSPACE_NOT_INITIALIZED` | 409 | Workspace has no connected cloud account or baseline config | Run onboarding/connect account flow first |
| `CLOUD_ACCOUNT_INVALID` | 400 | Credential/profile data invalid | Re-select profile/role and retry |
| `CLOUD_PREFLIGHT_FAILED` | 422 | IAM/quota/capacity checks failed | Review failed checks and remediate |
| `DEVICE_TEMPLATE_UNSUPPORTED` | 400 | Requested template not supported in region/profile | Choose supported template/region pair |
| `DEVICE_NOT_FOUND` | 404 | Device id unknown or purged | Refresh device inventory |
| `DEVICE_STATE_CONFLICT` | 409 | Action invalid for current lifecycle state | Wait for state transition or select valid action |
| `STREAM_NEGOTIATION_FAILED` | 502 | WebRTC/DCV/scrcpy signaling failed | Retry session open; inspect diagnostics |
| `SNAPSHOT_UNAVAILABLE` | 409 | Snapshot strategy not supported for device family/state | Use family-appropriate snapshot workflow |
| `RECIPE_VALIDATION_FAILED` | 422 | Recipe schema or inputs invalid | Fix schema/input contract and rerun |
| `TEST_RUN_FAILED` | 500 | Test orchestration failed unexpectedly | Inspect artifact bundle and run logs |
| `ARTIFACT_NOT_FOUND` | 404 | Artifact id/path not present | Refresh list or verify run completion |
| `COST_CAP_EXCEEDED` | 403 | Operation would exceed hard cap | Increase cap or stop existing spend |
| `DANGEROUS_OPERATION_CONFIRMATION_REQUIRED` | 412 | Dangerous tool/action attempted without confirmation | Reissue call with confirmed elicitation flow |
| `SECRET_REF_NOT_FOUND` | 404 | Secret reference does not exist in broker backend | Create/rename secret reference |
| `SECRET_INJECTION_DENIED` | 403 | Policy denied secret injection for caller/tool | Update permission mode or use operator flow |
| `MCP_CLIENT_UNAUTHORIZED` | 401 | Invalid/expired MCP token | Rotate token and reconnect |
| `MCP_TOOL_NOT_ALLOWED` | 403 | Client permission mode disallows tool group | Grant scope or choose permitted tool |
| `MCP_EXPECTED_SCREEN_VERSION_MISMATCH` | 409 | Optimistic action guard failed | Re-observe and retry action |
| `AWS_RATE_LIMITED` | 429 | Upstream API throttling | Retry with backoff; reduce burst |
| `INTERNAL_RUNTIME_AGENT_UNAVAILABLE` | 503 | Runtime agent channel is down | Re-establish tunnel/agent and retry |

## 4.2.2 Error envelope

All API and MCP errors return:

- `code` (stable identifier),
- `message` (human-readable summary),
- `details` (machine-readable context),
- `retryable` (boolean),
- `correlation_id` (trace id for support).
