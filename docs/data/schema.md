---
doc_id: "21.1"
title: "database schema"
section: "Data"
status: "current"
summary: "Physical persistence plan for DeviceLab metadata, lifecycle state, evidence, and cost caches."
updated: "2026-05-17"
---

# Database Schema
<!-- derived from: spec/spec.md (DeviceLab product section), idea.md §8 §17 -->

## Storage approach

- Primary: local SQLite for control-plane metadata.
- Optional: Litestream replication to user-owned S3 bucket.
- Scope: stores metadata, lifecycle state, recipes, artifacts/evidence indices, and audit/cost records.
- Excludes: bulk media payload blobs (stored as files/object storage with metadata pointers).

## Table groups

1. **Workspace/account:** `workspace`, `cloud_account`.
2. **Provisioning/runtime:** `device_template`, `device_profile`, `device`, `tunnel`, `warm_pool_slot`, `snapshot`.
3. **Sessions and automation:** `mcp_client`, `session`, `recipe`, `test_run`.
4. **Observability and audit:** `evidence`, `artifact`, `audit_event`.
5. **Safety and economics:** `secret_ref`, `cost_estimate`.

## Join patterns

- Dashboard lists: `device` joined with `device_template`, `device_profile`, and latest `session`.
- Replay timeline: `session` -> `evidence` (ordered by created timestamp).
- Cost summary: active `device` + cached `cost_estimate` keyed by service attributes.
- Test artifact retrieval: `test_run` -> `artifact`.

## Index rationale

- Composite index on `device(state, region, updated_at)` accelerates active device views.
- `evidence(session_id, created_at DESC)` supports replay scrubber pagination.
- `audit_event(at DESC)` supports incident triage windows.
- `cost_estimate(service_code, attributes_hash, expires_at)` keeps pricing lookups cheap.

## Retention and cleanup

- `evidence` and `audit_event` default retention: 30 days (configurable).
- Artifact metadata can be soft-deleted; blobs are garbage-collected by cleanup jobs.
- Device and snapshot soft-delete preserves auditability before purge.
