# SECURITY.md

Vulnerability disclosure and security expectations for this repository. For deep references see **[docs/security/README.md](docs/security/README.md)**.

## Supported versions

Security fixes are applied to maintained release lines. At template initialization, treat **current `main` / latest tag** as supported.

| Version | Supported |
|---------|-----------|
| Latest release / `main` | Yes |
| Older major versions | Only if explicitly listed in release notes |

Update this table when you cut releases and drop old lines.

## Reporting a vulnerability

1. **Do not** open a public GitHub issue for undisclosed security vulnerabilities.
2. Use **GitHub Security Advisories**: open the repository **Security** tab and choose **Report a vulnerability**.
3. If GitHub is unavailable, email **`security@example.com`** (replace with your project contact during initialization from `IDEA.md`).
4. Include: short description, steps to reproduce, suspected impact, and optional fix ideas.
5. **Acknowledgment:** we aim to acknowledge within **48 hours** and provide a substantive update within **7 days** (best effort).
6. **Disclosure:** please allow **90 days** for a fix before public disclosure, unless agreed otherwise.

Replace the placeholder security email when you initialize a real project.

## Security policy

- **Secrets** belong in environment variables or a secret manager — never in git. CI runs secret and dependency scans.
- **Dependencies:** Dependabot and `make security:scan` (or CI equivalent) track known CVEs in dependencies.
- **Containers:** images should be scanned (e.g. Trivy) before production deploy.
- **Auth:** JWT access tokens are short-lived; refresh and rotation patterns are documented under **`docs/security/`**.
- **Multi-tenancy:** tenant scope is enforced in services/repositories — see architecture docs.

## Accepted risks

Known accepted risks (CVEs deferred, compensating controls) live in **[docs/security/accepted-risks.md](docs/security/accepted-risks.md)**. Each entry should include review date and owner.
