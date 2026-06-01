---
doc_id: "25.5"
title: "Phase 12 — Root & Cloud Infra Settings"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-06-01"
---

# Phase 12 — Root & Cloud Infra Settings

**Progress: 0%** `░░░░░░░░░░` — planned

## Objective

Give the operator a single **server-level settings** surface for the infrastructure and policy the
application needs: cloud (AWS) connection details, the local host resource budget, streaming defaults,
MCP defaults, snapshot storage, and security/audit configuration. All cloud secrets go through
`keyring`/SecretRef (no plaintext), and the control plane stays localhost-only. This phase wires
settings into the services built in Phases 08–10.

Read first: `interactive-workspace-plan.md` (invariants) and existing `apps/web/src/routes/_layout/
settings.tsx`, `apps/api/app/core/config.py`.

---

## Settings groups (the deliverable)

| Group | Keys (representative) | Backed by |
|-------|----------------------|-----------|
| **Cloud infra (AWS, BYOC)** | credential source (env/profile/role-arn via **SecretRef**), default region, VPC/subnet ids, default instance types per family, artifact S3 bucket, **coturn/STUN** endpoints + creds | `keyring`, CloudAccount, `stream/ice.py` (09-04) |
| **Local host budget** | total RAM/vCPU/disk for devices, **reserved headroom %**, default placement policy, image + snapshot storage path, base image registry | ResourceLedger (08-07), placement (07-06) |
| **Streaming** | default codec (H.264), bitrate caps (local/cloud), default display profile (smooth/sharp_text), max concurrent streams, WebCodecs-canvas opt-in default | stream profiles (09-15), gateway |
| **MCP** | global enable, default per-device exposure, default role, session-token TTL, gateway bind host (**loopback enforced**) | mcp gateway, permissions |
| **Snapshots** | storage path, retention, max count, compression/dedup | SnapshotLibrary (10-02) |
| **Security / audit** | audit log path, keyring backend, dangerous-mode policy, log-redaction patterns | audit_log, log bus (08-10) |

---

## Task batches and dependencies

```
Batch A (settings backend)
  12-01  Settings model + service (typed groups, persisted, validated)
  12-02  Cloud-infra settings via SecretRef (no plaintext) + validation/test-connection
  12-03  Local-host-budget settings → ResourceLedger (live re-read of totals/headroom)

Batch B (wire into services)
  12-04  Streaming settings → ICE/profiles/bitrate caps
  12-05  MCP settings → exposure default, role default, token TTL, loopback bind guard
  12-06  Snapshot + security/audit settings wiring

Batch C (frontend)
  12-07  Settings UI: grouped sections, secret-masked inputs, test-connection buttons

Batch D (docs)
  12-08  Settings reference + first-run configuration guide
```

---

## Task 12-01: Settings model + service

**Files:** `apps/api/app/models.py` (`AppSetting` table or typed settings rows); 
`apps/api/app/services/settings.py` (new); Alembic migration.

Typed, grouped, persisted settings with defaults sourced from `core/config.py`. Service exposes
`get_group(name)` / `update_group(name, values)` with per-key validation. Changes emit audit events.

**Tests:** `test_settings_defaults_from_config`, `test_update_group_validates`,
`test_settings_change_emits_audit`.

**Do not:** store secrets in this table — secret-bearing values are SecretRefs (12-02).

---

## Task 12-02: Cloud-infra settings via SecretRef

**Files:** `services/settings.py` (cloud group); reuse `keyring`/SecretRef + CloudAccount.

AWS credential source, region, VPC/subnet, instance-type defaults, artifact bucket, coturn/STUN. All
secret material (access keys, TURN creds) stored via **SecretRef/`keyring`** — the settings row holds
only references. A **test-connection** action validates AWS reachability and (if set) coturn.

**Tests:** `test_cloud_settings_store_secret_as_ref`, `test_test_connection_reports_status`,
`test_no_plaintext_secret_in_settings_row`.

**Do not:** ever return raw secrets to the client or put them in logs (redaction + invariant).

---

## Task 12-03: Local-host-budget settings → ledger

**Files:** `services/settings.py` (host group); wire to `services/local/ledger.py` (08-07).

Operator sets device RAM/vCPU/disk budget + headroom %, storage paths, placement default. The
ResourceLedger reads these live so changing the budget immediately affects admission (with a guard
that the new budget can't be set below current commitments without a force/confirm).

**Tests:** `test_budget_change_updates_ledger_totals`,
`test_cannot_set_budget_below_current_commitment_without_force`.

**Do not:** allow a silent over-commit by lowering the budget under live devices.

---

## Task 12-04: Streaming settings wiring

**Files:** wire `stream/ice.py`, `stream/profiles.py`, gateway to the streaming group.

Default codec/bitrate caps/display profile/max concurrent streams/WebCodecs default flow from
settings. Cloud STUN/TURN endpoints come from the cloud group (12-02).

**Tests:** `test_default_profile_applied_to_new_stream`, `test_bitrate_caps_enforced`.

---

## Task 12-05: MCP settings wiring

**Files:** wire mcp gateway/permissions to the MCP group.

Global enable, default per-device exposure (`mcp_exposed` default), default role, session-token TTL,
and a **loopback bind guard** that refuses any non-loopback MCP bind host (localhost-only invariant).

**Tests:** `test_mcp_default_exposure_applied`, `test_mcp_bind_guard_rejects_non_loopback`,
`test_token_ttl_from_settings`.

---

## Task 12-06: Snapshot + security/audit wiring

**Files:** wire SnapshotLibrary (10-02), audit log, log redaction to their groups.

Snapshot storage path/retention/max/compression; audit log path; keyring backend; dangerous-mode
policy; configurable log-redaction patterns for the device log bus (08-10).

**Tests:** `test_snapshot_retention_enforced`, `test_custom_redaction_pattern_applied`.

---

## Task 12-07: Settings UI

**Files:** extend `apps/web/src/routes/_layout/settings.tsx`; new grouped section components.

Grouped sections matching the table; **secret-masked** inputs (write-only, show "configured");
test-connection buttons (AWS, coturn) with status; the host-budget editor shows the live ledger HUD
(11-12) so the operator sees headroom while editing.

**Tests:** `settings renders all groups`, `secret inputs are write-only/masked`,
`test-connection shows status`.

**Do not:** display stored secret values; never echo them back.

---

## Task 12-08: Docs

**Files:** `docs/operations/settings-reference.md` (new); update first-run/onboarding docs.

Document every setting, its default, its effect, and the SecretRef handling; a first-run checklist
(connect AWS or go fully local; set host budget; pick streaming defaults).

---

## Exit criteria

- An operator configures **all** required infra/policy from one settings surface: AWS (via SecretRef,
  no plaintext), local host budget (live-wired to the ledger), streaming, MCP, snapshots, security.
- Test-connection validates AWS and coturn.
- Lowering the host budget below live commitments is guarded; MCP bind is loopback-guarded; secrets
  are never returned to the client or logged.
- Settings changes are audited.
