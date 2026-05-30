---
doc_id: "18.0"
title: "Docs overview"
section: "Root"
summary: "Documentation hub. Index of all doc sections with one-line descriptions and links."
updated: "2026-04-17"
---

# 18.0 — Docs overview

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: README.md (root), AGENTS.md §Navigation -->

**Purpose:** Documentation hub. Index of all doc sections with one-line descriptions and links. Per spec §26.5 item 111.

## 18.0.1 Documentation Structure

Ordered list of every docs/ subdirectory with description and link to its README. Grouped by purpose:

**Getting started:**
- [getting-started/](getting-started/README.md) — Prerequisites and quickstart from clone to green dev

**Understanding the system:**
- [architecture/](architecture/README.md) — System design, bounded contexts, data layer, auth
- [api/](api/README.md) — Endpoint catalog and error codes
- [queue/](queue/queue-system-overview.md) — Agent work queue: concepts, lifecycle, intelligence
- [glossary.md](glossary.md) — Ubiquitous language and domain glossary

**Operating the system:**
- [development/](development/README.md) — Local setup, coding standards, testing, env vars
- [operations/](operations/README.md) — Docker, Kubernetes, observability, backups, rollback
- [security/](security/README.md) — Threat model, secrets, incident response, token lifecycle
- [runbooks/](runbooks/README.md) — Failure scenario runbooks (API down, DB failure, JWT rotation)

**Agent and human governance:**
- [procedures/](procedures/README.md) — Canonical SOPs for recurring workflows (agents first)
- [BRAINSTORM/](BRAINSTORM/README.md) — Read-only ideation space; one brainstorm file = whole idea; pipeline splits into **many** queue rows
- [agents/](agents/README.md) — Human supervision of agent work
- [prompts/](prompts/README.md) — Prompt library conventions and index
- [adr/](adr/README.md) — Architecture Decision Records

**Quality and releases:**
- [quality/](quality/README.md) — Testing strategy, coverage policy, flake policy
- [release/](release/README.md) — Versioning, promotion path, changelog guide
- [repo-governance/](repo-governance/README.md) — Improvement loops, audits, procedure drift
- [roadmap/](roadmap/README.md) — Long-term and phase-by-phase implementation plans

**Integrations (vendor / upstream):**
- [integrations/](integrations/README.md) — Mechanical import workflows (git/rsync), SHA pins, ADR cross-links

**Optional profiles:**
- [optional-clients/](optional-clients/web.md) — Web and mobile profile documentation
- [troubleshooting/](troubleshooting/README.md) — Common issues and solutions

<!-- AUTO_INDEX_START -->

## 18.0.2 Auto-generated index

_Machine listing of top-level docs paths — see sections above for curated descriptions._

- [adr/](adr/README.md)
- [agents/](agents/README.md)
- [BRAINSTORM/](BRAINSTORM/README.md)
- [api/](api/README.md)
- [architecture/](architecture/README.md)
- [development/](development/README.md)
- `generated/`
- [getting-started/](getting-started/README.md)
- [glossary](glossary.md)
- [operations/](operations/README.md)
- `optional-clients/`
- [procedures/](procedures/README.md)
- [prompts/](prompts/README.md)
- [quality/](quality/README.md)
- `queue/`
- [release/](release/README.md)
- [repo-governance/](repo-governance/README.md)
- [integrations/](integrations/README.md)
- [roadmap/](roadmap/README.md)
- [runbooks/](runbooks/README.md)
- [security/](security/README.md)
- [troubleshooting/](troubleshooting/README.md)

<!-- AUTO_INDEX_END -->
