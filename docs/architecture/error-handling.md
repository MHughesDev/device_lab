---
doc_id: "2.7"
title: "error handling"
section: "Architecture"
summary: "Cross-cutting error handling strategy."
updated: "2026-04-17"
---

# 2.7 — error handling

<!-- Optional per spec §26.12 item 400 -->

**Purpose:** Cross-cutting error handling strategy. Per spec §26.12 item 400.

## 2.7.1 Error Hierarchy

AppError hierarchy from apps/api/app/exceptions.py. Base class structure, HTTP status mappings, stable error codes.

## 2.7.2 Error Response Shape

Standard JSON error envelope: {"error": {"code": "...", "message": "..."}}. Never expose stack traces externally.

## 2.7.3 Error Propagation

Service raises AppError subclass → global exception handler in middleware.py translates → structured JSON response. Layer responsibilities: repositories translate SQLAlchemy errors at the adapter boundary.

## 2.7.4 Client Handling Guide

How API clients should handle each error category: 401 (re-auth), 429 (backoff), 503 (retry with backoff), 422 (fix request).
