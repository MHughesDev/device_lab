---
doc_id: "24.2"
title: "Phase 01 — Local foundation"
section: "Roadmap"
status: "complete"
completion: "100%"
updated: "2026-05-31"
---

# Phase 01 — Local Foundation

**Progress: 100%** `██████████` — complete

## Objective

Stand up a trustworthy local control plane that any developer can clone, start, and understand. By the end of this phase, the API is running on localhost, the database migrates cleanly, the device FSM is wired, the MCP gateway skeleton exists, and the web UI shows a status screen. No cloud resources are provisioned — everything is stubs and contracts.

---

## OSS pulled in this phase

| Repo / package | What we take | Where it lands |
|----------------|-------------|----------------|
| `pytransitions` (`pip install transitions`) | `Machine` class for device FSM | `apps/api/app/services/device_fsm.py` |
| `mcp` / FastMCP (`pip install mcp`) | FastMCP server, tool registration scaffold, transport mount | `apps/api/app/mcp/gateway.py` |
| `lulzasaur9192/agent-audit-log-examples` | ~100 lines of HMAC-SHA256 hash-chain logic (MIT, copy-not-install) | `apps/api/app/core/audit_log.py` |

---

## Implementation tasks

### 1. Baseline sanity + localhost hardening

Files: `apps/api/app/core/config.py`, `compose.yml`, `.env.example`

- Add `BIND_HOST` setting defaulting to `127.0.0.1` (never `0.0.0.0`).
- Add `DANGEROUS_MODE` flag defaulting to `false`.
- Add startup assertion: if `BIND_HOST != "127.0.0.1"` and not explicitly overridden via env, raise at import time.
- Update `compose.yml` so API and web ports bind `127.0.0.1` by default.
- Strip all template placeholder copy from `.env.example`; add DeviceLab-specific vars with comments.

### 2. DeviceLab data model scaffold

Files: `apps/api/app/models.py`, `apps/api/app/alembic/versions/`

Add SQLModel entities:

```
Workspace          id (uuid), name, created_at, settings_json
CloudAccount       id, workspace_id, provider, account_id, display_name,
                   status, last_preflight_at, preflight_summary_json
DeviceTemplate     id, family, name, description, capability_json, supported_regions
Device             id, template_id, workspace_id, family, state, phase,
                   provider_ids_json, cost_estimate, tags_json, created_at, updated_at
AuditEvent         id, workspace_id, actor, action, target_type, target_id,
                   decision, metadata_json, created_at, hash, prev_hash
```

Create a clean Alembic migration. Remove the template `Item` model entirely.

### 3. Device FSM

Files: `apps/api/app/services/device_fsm.py`

Use `pytransitions` (`pip install transitions`):

```
States:
  requested → preflight_blocked → provisioning → bootstrapping_agent
  → ready → stopping → stopped → terminating → terminated → failed

Transitions:
  preflight_fail:   requested           → preflight_blocked
  preflight_pass:   requested/blocked   → provisioning
  provision_done:   provisioning        → bootstrapping_agent
  agent_ready:      bootstrapping_agent → ready
  stop:             ready               → stopping
  stop_done:        stopping            → stopped
  start:            stopped             → provisioning
  terminate:        ready/stopped/...   → terminating
  terminate_done:   terminating         → terminated
  fail:             * (any)             → failed
```

The FSM persists state to `Device.state` synchronously before any async cloud call. Every transition emits an `AuditEvent` via `audit_log.append_event()`.

### 4. Workspace + health endpoints

Files: `apps/api/app/api/routes/workspace.py`, `apps/api/app/api/routes/health.py`

```
GET /api/v1/health
  → { status, db_ok, version, timestamp }

GET /api/v1/workspace
  → { id, name, version, bind_host, dangerous_mode,
      capabilities: {
        aws_connect: bool,
        device_lifecycle: bool,
        mcp_gateway: bool,
        streaming: bool,
        recipes: bool
      },
      cloud_accounts: [{ id, provider, status }] }
```

All capability flags return `false` at this phase — they flip to `true` as each phase ships.

### 5. MCP gateway skeleton

Files: `apps/api/app/mcp/gateway.py`, `apps/api/app/mcp/tools/__init__.py`

Stand up FastMCP mounted at `/mcp` via `app.mount()` in `apps/api/app/main.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DeviceLab", version="0.1.0")

@mcp.tool()
def workspace_status() -> dict:
    """Return workspace capabilities and cloud account status."""
    ...

@mcp.tool()
def list_devices() -> list[dict]:
    """List all devices and their current lifecycle state."""
    ...
```

Tools return `{"status": "not_implemented", "phase": 1}` at this stage. The gateway existing and responding to capability handshake is the deliverable.

### 6. Web UI — status screen

Files: `apps/web/src/routes/_layout/index.tsx`, `apps/web/src/components/Workspace/StatusCard.tsx`

Replace the template Items page with a DeviceLab status screen:
- Workspace name + control plane version
- Capability flags (aws_connect, device_lifecycle, mcp_gateway) as enabled/disabled badges
- Cloud accounts list — empty state with "Connect AWS account" CTA (phase 02 target)
- Health indicator (green/red dot calling `/api/v1/health`)

Keep template auth, sidebar, and theme infrastructure. Only replace main content area.

### 7. Audit log foundation

Files: `apps/api/app/core/audit_log.py`

Mob ~100 lines from `lulzasaur9192/agent-audit-log-examples` (MIT license). Core pattern:

```python
import hashlib, hmac, json
from datetime import datetime, timezone

def compute_hash(entry: dict, prev_hash: str, secret_key: bytes) -> str:
    payload = json.dumps({**entry, "prev_hash": prev_hash}, sort_keys=True)
    return hmac.new(secret_key, payload.encode(), hashlib.sha256).hexdigest()

def append_event(db, *, actor, action, target_type, target_id, metadata, decision="allow"):
    last = db.exec(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(1)).first()
    prev_hash = last.hash if last else "genesis"
    entry = {
        "actor": actor, "action": action,
        "target_type": target_type, "target_id": target_id,
        "decision": decision, "metadata": metadata,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entry["hash"] = compute_hash(entry, prev_hash, settings.audit_secret_key)
    entry["prev_hash"] = prev_hash
    db.add(AuditEvent(**entry))
    db.commit()
```

Secret key sourced from `Settings` (env var, never hardcoded).

### 8. Cleanup template boilerplate

- Delete `apps/api/app/api/routes/items.py`
- Remove `Item` from `models.py`
- Remove items router from `apps/api/app/api/main.py`
- Update `apps/web/src/routes/` to remove Items pages
- Keep: `User`, auth routes, sidebar shell, health route

---

## Exit criteria

- `make dev` starts API + web UI; both bind `127.0.0.1` only — verified by socket inspection test.
- `GET /api/v1/workspace` returns valid JSON with all capability flags `false`.
- `GET /api/v1/health` returns `200` with `db_ok: true`.
- `GET /mcp` responds with valid MCP capability handshake.
- Device FSM unit tests cover all valid transitions and all invalid transition rejections.
- Audit log unit test verifies HMAC chain integrity across 3+ chained events and detects tampering.
- Template `Item` model and routes are gone from both API and web.
- No service binds `0.0.0.0` in default config.
