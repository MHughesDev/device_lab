---
doc_id: "24.2"
title: "Phase 01 - Local foundation"
section: "Roadmap"
status: "current"
completion: "0%"
summary: "Detailed implementation plan for making DeviceLab locally runnable, localhost-only by default, documented, and ready for product feature work."
updated: "2026-05-30"
---

# Phase 01 - Local Foundation
<!-- derived from: queue/queue.csv Q-101, docs/operations/deployment.md, spec/spec.md section 18 -->

## Objective

Create a trustworthy local foundation for all later DeviceLab work. By the end of this phase, an operator should be able to start the local control plane, understand what is intentionally not implemented yet, and verify that no runtime service binds publicly by default.

## Scope

In scope:

- Local startup path for API, web UI, and MCP gateway placeholders.
- Localhost-only defaults for control-plane services.
- Workspace configuration shape and health/status projection.
- Documentation that explains the current runnable path.
- Initial validation commands and handoff conventions.

Out of scope:

- Real AWS account provisioning.
- Real device lifecycle implementation.
- Production packaging.
- Device streaming beyond contract placeholders.

## Implementation Sequence

1. Inventory actual repo state.
   Confirm whether `apps/api`, `apps/web`, `compose.yml`, `Makefile`, scripts, and MCP gateway files exist. If the repo is documentation-only, create queue rows for missing baseline import before product feature work.

2. Define local configuration defaults.
   Add settings for host, port, database URL, MCP mode, feature flags, and dangerous-mode enablement. Default all bind hosts to `127.0.0.1`.

3. Expose workspace status.
   Implement or document a minimal `/api/v1/workspace` contract returning product version, local profile, enabled capabilities, cloud account status, and health summaries.

4. Document local startup.
   Update operational and getting-started docs with exact commands, expected ports, prerequisites, and shutdown steps.

5. Add safety assertions.
   Add tests or startup checks that fail if the default host is public, dangerous mode is enabled without an explicit setting, or a required local secret is missing.

6. Prepare MCP config path.
   Define the shape of local MCP config output even if the tools are not implemented yet. This prevents first-run wizard work from inventing a second model.

## Data and Config Details

| Item | Direction |
|---|---|
| Workspace identity | Single local workspace by default; multi-workspace support can be a later extension. |
| Settings source | Environment variables with documented defaults, avoiding secrets in checked-in files. |
| Local database | Prefer SQLite for earliest local-only bootstrap if the full Postgres baseline is absent; record any deviation in ADR/docs. |
| Feature flags | `aws_connect`, `device_lifecycle`, `mcp_gateway`, `dangerous_mode`, `streaming`, `recipes`. |

## API and UI Contracts

- `GET /api/v1/workspace` returns local system status.
- `GET /api/v1/health` returns liveness and dependency checks.
- UI first screen shows setup status and next required action, not marketing content.
- MCP config endpoint may return "not ready" status with precise missing prerequisites.

## Testing and Verification

- Run the repo's docs-map check if scripts are present.
- Run startup smoke commands for API/web once code exists.
- Add tests for default host binding and feature flag defaults.
- Manually inspect docs for stale template-only references.

## Exit Criteria

- A new agent can follow docs from clone to local status screen.
- No default local service binds to `0.0.0.0`.
- Missing product implementation is represented as explicit disabled capabilities, not broken links.
- Phase 02 can begin without inventing new local configuration concepts.

