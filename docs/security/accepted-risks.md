---
doc_id: "16.1"
title: "accepted risks"
section: "Security"
summary: "Accepted CVEs and review dates; links to dependency audit."
updated: "2026-04-17"
---

# 16.1 — accepted risks

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/security/README.md, AGENTS.md §11 (Escalation) -->

**Purpose:** Accepted CVEs and review dates; links to dependency audit.

## 16.1.1 Overview

Accepted CVEs and review dates; links to dependency audit. See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

## 16.1.2 Accepted findings

| CVE / ID | Component | Rationale | Review |
|----------|-----------|-----------|--------|
| [CVE-2024-23342](https://github.com/advisories/GHSA-wj6h-64fc-37mp) | PyPI `ecdsa` (transitive via `python-jose`) | Minerva timing issue in pure-Python ECC; upstream does not treat side-channel attacks as in scope and there is no patched release that satisfies scanners. JWT verification paths used here do not rely on `ecdsa` signing APIs. Prefer migrating off `python-jose` / auditing transitive crypto in a future hardening pass. | 2026-04-14 |
| [CVE-2025-69720](https://nvd.nist.gov/vuln/detail/CVE-2025-69720) | Debian `ncurses` (API image) | Template uses `python:3.12-slim`; scanner reports fixed versions when Debian publishes. Track via image digest bumps and `apt-get upgrade` in Dockerfile. | 2026-04-14 |
| [CVE-2026-27135](https://nvd.nist.gov/vuln/detail/CVE-2026-27135) | Debian `libnghttp2` (API image) | Same as above; acceptable until base image provides patched packages. | 2026-04-14 |
| [CVE-2026-29111](https://nvd.nist.gov/vuln/detail/CVE-2026-29111) | Debian `systemd` / `libudev` (API image) | Transitive libs in slim image; mitigated by minimal attack surface; rebuild when upstream slim updates. | 2026-04-14 |
