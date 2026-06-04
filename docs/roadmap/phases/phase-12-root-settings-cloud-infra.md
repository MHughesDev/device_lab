---
doc_id: "25.5"
title: "Phase 12 — Root & Cloud Infra Settings"
section: "Roadmap"
status: "complete"
completion: "100%"
updated: "2026-06-02"
---

# Phase 12 — Root & Cloud Infra Settings

**Progress: 100%** `██████████` — complete

## What shipped

### Batch A — settings backend (12-01, 12-02, 12-03)

- **`AppSetting` model** (`apps/api/app/models.py`) — workspace-scoped key-value table with
  `group`, `key`, `value` (JSON-encoded), `is_secret_ref` flag. Unique on `(workspace_id, group, key)`.
- **Alembic migration** `b3c4d5e6f7a8_phase12_app_settings.py`
- **`settings_service.py`** — typed `DEFAULTS` for 6 groups; `get_group()` / `update_group()` /
  `get_all()`; per-group validation (MCP loopback guard, streaming profile enum, headroom 0–50 %);
  secret keys stored via `keyring` with `is_secret_ref=True`; reads return `"***"` sentinel;
  every write emits an audit event via the HMAC chain.

### Batch B — wire into services (12-04, 12-05, 12-06)

- **`stream/ice.py`** — `_cloud_ice()` and `load_from_settings()` read STUN/TURN from AppSettings
  first (resolving SecretRefs via keyring), falling back to env vars. No secrets logged.
- **`services/local/ledger.py`** — `ResourceLedger.apply_settings()` reads the `host` group and
  updates `_headroom_mb`, `_caps.total_ram_mb`, and `_caps.total_vcpu`; guards against lowering
  below current committed resources.

### Batch C — frontend (12-07)

- **`components/settings/InfraSettings.tsx`** — six grouped sections (Cloud, Host, Streaming,
  MCP, Manifests, Security) each with Save button and dirty tracking.
  - Secret fields use `SecretInput` (write-only; shows "configured" when "***" returned).
  - Cloud section includes a Test AWS connection button with inline status.
  - Host section shows budget inputs; MCP bind-host labelled as loopback-only.
- **`routes/_layout/settings.tsx`** — adds Infrastructure tab (superuser only).

### Batch D — docs (12-08)

- **`docs/operations/settings-reference.md`** — every key, default, description, SecretRef
  markers, and first-run checklist.

## Exit criteria — status

| Criterion | Status |
|-----------|--------|
| All 6 setting groups persisted and validated | ✅ |
| Secret values stored via keyring/SecretRef; never returned to client | ✅ |
| MCP bind host loopback guard enforced server-side | ✅ |
| Host budget lower-than-committed guard | ✅ |
| Settings changes emit audit events | ✅ |
| STUN/TURN config wired into ICE (ice.py) | ✅ |
| Host budget wired into ResourceLedger (ledger.py) | ✅ |
| Test-connection validates AWS and reports caller identity | ✅ |
| Infrastructure tab in Settings UI (superuser only) | ✅ |
| Secret inputs write-only / masked | ✅ |
| Settings reference docs | ✅ |
