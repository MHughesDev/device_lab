# skills/security/secret-handling.md

<!-- CROSS-REFERENCES -->
<!-- - Machinery: skills/security/secret-scanner.py -->
<!-- - Related rule: .cursor/rules/security.md -->
<!-- - Related docs: docs/security/secrets-management.md -->

**Purpose:** [FULL SKILL] How to handle secrets correctly: env-only sourcing, rotation procedures, never in code/logs, .env.example documentation. Per spec §26.4 item 72.

## Purpose

One paragraph. Secrets in code are a critical security vulnerability. This skill establishes the complete policy for secret handling: where secrets live (env vars only), how to document them (.env.example), how to detect accidental leakage (scanner), and what to do when a secret is leaked (immediate rotation).

## When to Invoke

- When adding any new secret to the application (API key, JWT secret, database password)
- When reviewing any PR that touches authentication, configuration, or external services
- When investigating a potential secret leak
- On quarterly security review cadence

## Prerequisites

.cursor/rules/security.md read. docs/security/secrets-management.md read. Access to the secret management system (password manager, vault, etc.).

## Relevant Files/Areas

- `apps/api/app/config.py` — the ONLY place secrets are read via BaseSettings
- `.env.example` — documents all secrets with CHANGEME placeholders
- `.pre-commit-config.yaml` — detect-secrets hook prevents accidental commits
- `skills/security/secret-scanner.py` — scan for leaked secrets in codebase
- `docs/security/secrets-management.md` — policy documentation

## Step-by-Step Method

Numbered steps:

**Adding a new secret**:
1. Add field to `Settings` class in `apps/api/app/config.py`:
   ```python
   stripe_api_key: str = Field(description="Stripe secret key for payment processing")
   ```
2. Add to `.env.example` with CHANGEME placeholder and comment:
   ```
   # Stripe API key — get from Stripe Dashboard → Developers → API keys
   STRIPE_API_KEY=sk_CHANGEME
   ```
3. Update `docs/development/environment-vars.md` (run `make docs:generate`)
4. Run `scripts/secret-scanner.py` to verify no real values in code

**Verifying no secrets in code**:
5. Run `python skills/security/secret-scanner.py --scan-path .`
6. Review findings: real secrets vs. examples/test values
7. False positives: add to `.secrets.baseline` via detect-secrets

**Secret leaked (emergency procedure)**:
8. STOP — do not panic
9. Rotate the secret immediately at the source (API provider, database, etc.)
10. Update the secret in all deployment environments
11. Search git history for the commit: `git log -S "SECRET_VALUE"`
12. File incident report per `docs/security/incident-response.md`
13. Remove from git history if not yet public (git filter-branch / BFG)

## Command Examples

- `python skills/security/secret-scanner.py` — scan for secrets
- `detect-secrets scan > .secrets.baseline` — update baseline
- `make security:scan` — run full security scan including secrets

## Validation Checklist

- [ ] All secrets sourced via BaseSettings only (no os.getenv() elsewhere)
- [ ] .env.example has CHANGEME placeholder for each secret
- [ ] .env.example comment explains what the secret is and how to get it
- [ ] secret-scanner.py passes with no new findings
- [ ] detect-secrets hook passes (pre-commit)
- [ ] No secrets in test fixtures with realistic format

## Common Failure Modes

- **Test secret looks real**: `api_key = "sk_test_abc123"` → detect-secrets flags it. Fix: use clearly fake values like `sk-FAKE-TEST-VALUE`.
- **Secret in log**: `logger.info(f"Connecting with key {api_key}")` → leaks in log files. Fix: never log secret values, only log presence: `logger.info("API key configured: %s", "yes" if api_key else "no")`.
- **Secret in error message**: exception includes config value. Fix: mask in exception handler.

## Handoff Expectations

New secret properly documented, scanner passes, PR description confirms secret is documented in .env.example.

## Related Procedures

docs/security/secrets-management.md, docs/security/incident-response.md

## Related Prompts

prompts/security_review_agent.md

## Related Rules

.cursor/rules/security.md (Secret Sourcing Rules section)

## Machinery

`skills/security/secret-scanner.py` — regex-based scanner for high-entropy strings and known secret patterns. Invoke: `python skills/security/secret-scanner.py --scan-path .` to scan all files, or `make security:scan` for the full security pipeline.
