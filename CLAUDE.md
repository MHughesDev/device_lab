# DeviceLab — agent context

## What this is

DeviceLab is an open-source, local-first, BYOC device testing platform. Control plane runs on developer's laptop. All cloud resources (EC2, Mac Dedicated Host, Device Farm) provision into the user's own AWS account. Devices are exposed to AI agents via MCP and to humans via a web UI.

## Current state

Pre-code. Spec and research are complete. The FastAPI + React + Docker Compose scaffold will be merged in next, then Phase 1 MVP work begins.

Do not attempt to run the app yet — there is no application code.

## Key files to read before working

1. `spec/spec.md` — authoritative spec; overrides everything else
2. `docs/product/end-state-capabilities.md` — full feature enumeration
3. `docs/roadmap/long-term-plan.md` — 6-phase build sequence
4. `docs/research/notes/oss-repo-candidates.md` — dependency decisions (locked; do not re-litigate)

## Architecture invariants

- **Localhost-only control plane** — no inbound ports, no cloud control plane, never expose the API to the internet
- **BYOC hard boundary** — all cloud resources go in the user's AWS account; DeviceLab never hosts devices
- **MCP first** — the primary agent interface is MCP; web UI is secondary
- **No plaintext secrets in model context** — SecretRef indirection always; use `keyring`
- **Append-only audit log** — HMAC-SHA256 hash chain; never mutate existing entries
- **Adapter SPI** — each device family is a versioned plugin; never put device-family-specific logic in the core

## Dependency decisions (locked)

Do not swap these without an ADR.

- WebRTC: `aiortc`
- MCP server: `mcp` via FastMCP
- Browser adapter: `browser-use`
- Android: `uiautomator2` + `adb`
- AWS pricing: `boto3` + `awspricing`
- Recipe DSL: `pypyr`
- Secrets: `keyring`
- Network proxy: `mitmproxy`
- AX tree scripts: copied from `viralmind-ai/accessibility-tree-parsers`
- Audit log: write from scratch (~100 lines HMAC-SHA256)
- Runtime agent: write from scratch (STF pattern reference)

## Working branch

Develop on `claude/kind-ride-LdQi9`. Push there. PR #1 is open.

## Phase 1 MVP tasks (start here once scaffold is in)

1. Stand up DeviceLab local-first runtime entrypoint with localhost-only control plane defaults
2. Implement device FSM using `pytransitions` (states: requested → preflight_blocked → provisioning → bootstrapping_agent → ready → stopping → stopped → terminating → terminated → failed)
3. Stub Linux adapter (EC2 launch + SSM bootstrap)
4. MCP gateway skeleton — per-device filtered tool manifest, capability handshake
5. Minimal web UI — device list, provision button, status badge

## Dev conventions (will apply once scaffold arrives)

- Backend: FastAPI + SQLModel + Postgres + Alembic
- Frontend: React 19 + Vite + TanStack Router/Query
- Tests: pytest (backend), Vitest (frontend)
- Lint: Ruff + mypy (backend), Biome (frontend)
- Containers: Docker Compose for local dev
