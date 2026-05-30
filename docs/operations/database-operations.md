---
doc_id: "6.3"
title: "database operations"
section: "Operations"
summary: "Database operations: VACUUM, indexes, pool tuning, slow queries."
updated: "2026-04-17"
---

# 6.3 — database operations

<!-- Optional per spec §26.12 item 402 -->

**Purpose:** Database operations: VACUUM, indexes, pool tuning, slow queries. Per spec §26.12 item 402.

## 6.3.1 VACUUM and ANALYZE

PostgreSQL maintenance: when to run VACUUM ANALYZE, autovacuum settings, monitoring table bloat.

## 6.3.2 Index Management

Creating indexes safely in production: CREATE INDEX CONCURRENTLY, monitoring usage, removing unused indexes.

## 6.3.3 Connection Pool Tuning

SQLAlchemy pool_size, max_overflow, pool_timeout settings. How to diagnose pool exhaustion.

## 6.3.4 Slow Query Identification

Enable pg_stat_statements, identify slow queries via pg_slow_statements, explain analyze patterns.
