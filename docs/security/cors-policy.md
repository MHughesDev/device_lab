---
doc_id: "16.2"
title: "cors policy"
section: "Security"
summary: "CORS origins and security rationale."
updated: "2026-04-17"
---

# 16.2 — cors policy

<!-- Optional per spec §26.12 item 403 -->

**Purpose:** CORS origins and security rationale. Per spec §26.12 item 403.

## 16.2.1 CORS Configuration

Allowed origins are defined in settings.api_cors_origins (env var API_CORS_ORIGINS). Never "*" in production. Local dev: http://localhost:3000, http://localhost:8000.

## 16.2.2 Security Rationale

Why we restrict CORS: prevent cross-origin requests from malicious sites. Allow credentials=True: needed for cookie-based auth if ever implemented. Allowed methods and headers list.

## 16.2.3 Per-Environment Settings

Dev: permissive (multiple localhost origins). Staging: staging domain only. Prod: production domain(s) only.
