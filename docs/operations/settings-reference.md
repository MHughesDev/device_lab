---
doc_id: "ops-04"
title: "Settings Reference"
section: "Operations"
updated: "2026-06-02"
---

# DeviceLab Settings Reference

All server-level settings are stored in the `appsetting` table (workspace-scoped key-value rows)
and exposed via `GET/PATCH /api/v1/settings/{group}`. The Settings UI is at `/settings` →
**Infrastructure** (superuser only).

**Security invariants:**
- Secret values (AWS credentials, TURN creds) are stored in the OS keychain via `keyring`/SecretRef.
  The database row holds only the SecretRef name with `is_secret_ref=True`.
- The API never returns raw secret values — reads return `"***"` for secret keys.
- MCP bind host is validated server-side to be loopback only (`127.0.0.1` or `::1`).
- Every settings change emits an audit event (HMAC chain, append-only).

---

## First-run checklist

1. **Cloud or local-only?**
   - Cloud (AWS): configure `cloud.credential_source` + test connection.
   - Local only: leave cloud group at defaults; set `host.placement_policy = local_only`.

2. **Set host budget** (optional): `host.device_ram_budget_mb`, `host.device_cpu_budget_cores`,
   `host.headroom_pct`. Defaults auto-detect from the host OS.

3. **Streaming defaults**: pick `streaming.default_profile` (`smooth` or `sharp_text`).

4. **MCP**: confirm `mcp.global_enabled = true` and set `mcp.default_role` to the least
   privilege your agents need.

---

## Group: `cloud`

| Key | Default | Description |
|-----|---------|-------------|
| `credential_source` | `"env"` | `env` · `profile` · `role` |
| `default_region` | `"us-east-1"` | AWS region for new devices |
| `default_vpc_id` | `null` | VPC to launch instances in |
| `default_subnet_id` | `null` | Subnet for EC2 instances |
| `linux_instance_type` | `"t3.medium"` | Default Linux EC2 type |
| `android_instance_type` | `"c8i.xlarge"` | Nested-virt Android |
| `windows_instance_type` | `"t3.large"` | Windows |
| `macos_instance_type` | `"mac2.metal"` | macOS Dedicated Host |
| `artifact_bucket` | `null` | S3 bucket for logs/snapshots |
| `stun_url` | `null` | STUN server URL (falls back to Google STUN) |
| `turn_url` ⚠ | `null` | coturn TURN URL (stored as SecretRef) |
| `turn_username` ⚠ | `null` | TURN credential (stored as SecretRef) |
| `turn_credential` ⚠ | `null` | TURN credential (stored as SecretRef) |
| `credential_profile` ⚠ | `null` | AWS profile name (SecretRef) |
| `credential_role_arn` ⚠ | `null` | IAM role ARN (SecretRef) |

⚠ = stored as SecretRef in keyring; API returns `"***"`.

**Test connection:** `POST /api/v1/settings/cloud/test-connection` calls STS
`GetCallerIdentity` and returns `{"status":"ok","detail":"..."}`.

---

## Group: `host`

| Key | Default | Description |
|-----|---------|-------------|
| `device_ram_budget_mb` | `null` | Total RAM for devices (null = auto from OS) |
| `device_cpu_budget_cores` | `null` | CPU cores for devices (null = auto) |
| `headroom_pct` | `20` | % of total RAM reserved for host OS (0–50) |
| `storage_path` | `"/var/lib/devicelab/images"` | Base image storage |
| `placement_policy` | `"local_first"` | `local_first` · `cloud_first` · `local_only` |
| `max_devices` | `10` | Maximum concurrent local devices |

**Guard:** lowering `device_ram_budget_mb` below current committed RAM is refused with a 422.

---

## Group: `streaming`

| Key | Default | Description |
|-----|---------|-------------|
| `default_codec` | `"h264"` | Video codec for WebRTC |
| `default_profile` | `"smooth"` | `smooth` (30fps/8Mbps) · `sharp_text` (12fps/4Mbps) |
| `local_bitrate_kbps` | `8000` | Bitrate cap for local devices |
| `cloud_bitrate_kbps` | `4000` | Bitrate cap for cloud devices |
| `max_concurrent_streams` | `8` | Max simultaneous interactive sessions |
| `webcodecs_canvas_default` | `false` | Default for WebCodecs low-latency path (11-11) |

---

## Group: `mcp`

| Key | Default | Description |
|-----|---------|-------------|
| `global_enabled` | `true` | Enable/disable the MCP gateway |
| `default_exposure` | `true` | Default `mcp_exposed` on device creation |
| `default_role` | `"observe"` | Default agent role (`observe`/`test`/`operate`/`admin`) |
| `token_ttl_minutes` | `60` | Session token lifetime |
| `bind_host` | `"127.0.0.1"` | **Loopback only** — enforced server-side |

---

## Group: `manifests`

| Key | Default | Description |
|-----|---------|-------------|
| `export_dir` | `"/var/lib/devicelab/manifests/export"` | Default export path |
| `import_dir` | `"/var/lib/devicelab/manifests/import"` | Auto-scan import path |
| `max_count` | `100` | Max manifests per workspace |
| `retention_days` | `90` | Age after which manifests are eligible for pruning |
| `validation_strictness` | `"standard"` | `permissive` · `standard` · `strict` |

---

## Group: `security`

| Key | Default | Description |
|-----|---------|-------------|
| `dangerous_mode` | `false` | Enables destructive ops without confirmation |
| `audit_log_path` | `"/var/lib/devicelab/audit.jsonl"` | HMAC-chained audit log path |
| `keyring_backend` | `"auto"` | `auto` · `system` · `file` |
| `log_redaction_patterns` | `[".*PASSWORD.*", ...]` | Regex patterns; matching field values → `***REDACTED***` |
