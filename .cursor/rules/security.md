---
alwaysApply: true
description: Security invariants. No secrets in code, token handling rules, tenant isolation checks, dependency review triggers.
---

# .cursor/rules/security.md

Security defaults for all work. Deep references: **`docs/security/`**, **`skills/security/`**, **`docs/procedures/validate-change.md`**.

## Secrets

1. Runtime secrets come from **environment** via **`Settings`** in **`apps/api/app/config.py`** — not scattered **`os.getenv()`**.
2. Never commit real credentials, tokens, or private keys.
3. Tests use obviously fake values from fixtures — not production-like secrets.
4. **`.env.example`** lists variables with safe placeholders.
5. If a secret is ever committed: **rotate**, remove from history per playbook, and follow **`docs/security/incident-response.md`**.

## JWT and auth (API)

1. Protected routes resolve the user via dependency-injected auth — not ad hoc decoding in handlers.
2. Validate signature, expiry, and required claims; align with config for issuer/audience when used.
3. Log **`user_id` / `tenant_id`**, never raw bearer tokens.

## Multi-tenancy

1. Tenant scope flows from auth + middleware into **`request.state`** (or equivalent).
2. Tenant-scoped queries always filter by **`tenant_id`** — helpers/mixins should make missing filters hard.
3. **`apps/api/tests/test_tenancy.py`** (or equivalent) must cover isolation scenarios before risky changes merge.

## Dependencies

1. Changing **`pyproject.toml`** → run **`make security:scan`** (or CI equivalent) before merge.
2. Document new direct dependencies in **`docs/development/dependency-management.md`** when policy requires.
3. Track accepted CVE risk in **`docs/security/accepted-risks.md`**.

## Never do this

1. String-concatenated SQL; use parameterized queries/ORM.
2. Disabling auth outside dedicated test configs.
3. Leaking stack traces to clients in production — use structured errors.
4. Running with **`DEBUG=true`** in real deployments.
5. Storing passwords without strong hashing (`passlib` / modern algorithms as configured).
6. **`eval` / `exec` / unsafe deserialization** on untrusted input.
7. Weak hashing for security properties (MD5/SHA-1 for passwords/secrets).
8. Logging passwords, raw JWTs, or API keys.
