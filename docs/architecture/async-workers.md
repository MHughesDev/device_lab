---
doc_id: "2.12"
title: "async workers"
section: "Architecture"
status: "current"
summary: "DeviceLab background worker inventory for provisioning, lifecycle orchestration, cost guardrails, and cleanup."
updated: "2026-05-17"
---

# Async Workers
<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §7 §9 §12 §17 -->

DeviceLab requires background execution for lifecycle orchestration and periodic safety checks. The default runtime is an in-process asyncio supervisor; a Redis-backed worker profile is optional for high parallelism.

## Task inventory

| Task | Trigger | Payload | Retry policy | Failure handling | Idempotency key |
|---|---|---|---|---|---|
| `provision_device` | create-device request | template/profile/account/region | exponential retry on transient AWS errors | mark device `Error` with structured reason | `device_id + requested_generation` |
| `bootstrap_runtime_agent` | post-provision hook | instance metadata + bootstrap version | up to 5 attempts | phase marker `installing_runtime` + actionable remediation | `device_id + agent_version` |
| `maintain_tunnel` | session start + heartbeat ticker | device endpoint + tunnel spec | immediate reconnect with capped backoff | emit session warning + degrade to reconnectable state | `device_id + tunnel_kind` |
| `poll_cost_guardrails` | periodic (1m) | active device list + pricing cache key | no hard retries, run next cycle | emit warning events, never crash scheduler | timestamp bucket |
| `sweep_orphan_resources` | periodic/nightly | tag selectors + account scope | continue-on-error per resource | produce cleanup report artifact + queue suggestions | `account_id + day` |
| `snapshot_job` | snapshot request | device id + snapshot strategy | per-family retries | snapshot status remains queryable with detailed error | `device_id + snapshot_request_id` |
| `warm_pool_reconcile` | periodic | template targets + current slots | bounded retries | downshift desired capacity and alert | `template_id + interval` |
| `artifact_bundle_build` | diagnostics/evidence export request | run/session identifiers | retry on filesystem/transient IO | return partial bundle + manifest of missing items | `bundle_request_id` |

## Operational rules

- Worker crashes must not orphan device state; lifecycle state transitions are persisted before side effects.
- Long-running jobs are externally observable through status endpoints/events.
- Retry loops must honor per-account rate limits and cost tiers.
- Jobs touching secrets resolve references at execution time and never persist plaintext.
