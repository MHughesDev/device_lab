---
doc_id: "6.10"
title: "deployment"
section: "Operations"
status: "current"
summary: "DeviceLab deployment model for local control plane and BYOC AWS bootstrap resources."
updated: "2026-05-17"
---

# Deployment
<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §13 -->

## Deployment targets

| Target | Scope | Notes |
|---|---|---|
| Local developer machine (default) | FastAPI + web UI + MCP gateway | Primary deployment mode; binds to localhost |
| User AWS account | Device runtime resources | Provisioned on demand per device and bootstrap stack |
| Optional long-running personal VM | Persistent control plane | Uses same local-first model plus backup replication |

## Ordered deployment steps

1. Configure local environment and start control plane containers/processes.
2. Open UI and connect AWS account credentials (profile/SSO/AssumeRole).
3. Run preflight checks (IAM, quota, region, capacity).
4. Optionally deploy bootstrap CloudFormation stack (VPC/IAM/SSM/S3/TURN helpers).
5. Create first Linux device and verify runtime agent channel.
6. Configure MCP client using generated local config.

## Post-deploy verification

- `workspace` status shows connected account and preflight pass.
- First device reaches `Ready` and opens an interactive stream.
- MCP capability handshake succeeds and returns tool groups.
- Cost summary endpoint returns non-empty estimate payload.

## Failed deploy handling

- Preflight failure: stop and remediate missing IAM/quota/capacity.
- Runtime agent/tunnel failure: collect diagnostics bundle and retry bootstrap.
- Cost cap misconfiguration: lower running resources and re-run guardrail checks.
