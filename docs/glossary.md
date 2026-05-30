---
doc_id: "18.1"
title: "glossary"
section: "Root"
summary: "Ubiquitous language and domain glossary. Defines terms used consistently across spec, code, and documentation."
updated: "2026-04-17"
---

# 18.1 — glossary

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: AGENTS.md §Navigation, docs/README.md -->

**Purpose:** Ubiquitous language and domain glossary. Defines terms used consistently across spec, code, and documentation. Per spec §26.12 item 374.

## 18.1.1 Purpose

This glossary is the single source of truth for term definitions in this repository. Agents and humans use these definitions when writing code, docs, and specs. Ambiguous terms are resolved here, not ad hoc.

## 18.1.2 Core Repository Terms

Table of repository-specific terms. Columns: Term, Definition, Used In. Rows:

| Term | Definition | Used In |
|------|-----------|---------|
| **Queue** | CSV-based agent work orchestration lane with strict lifecycle | queue/queue.csv, QUEUE_INSTRUCTIONS.md |
| **Queue item** | A single row in queue.csv representing a unit of agent work | queue/queue.csv |
| **Summary** | The elaborative description in queue item's summary column — the work contract | queue/queue.csv §summary |
| **Archive** | The historical record of completed/cancelled/superseded queue items | queue/queuearchive.csv |
| **Skill** | An executable playbook in skills/ for a recurring task type | skills/ |
| **Procedure** | A canonical SOP in docs/procedures/ for a named workflow | docs/procedures/ |
| **Prompt template** | A reusable LLM prompt in prompts/ for a recurring agent role | prompts/ |
| **Rule** | A constraint in .cursor/rules/ enforced on every agent interaction | .cursor/rules/ |
| **Profile** | An optional feature set (web, mobile, workers, ai-rag, multi-tenancy) | docker-compose.yml, .env.example |
| **Archetype** | The project type selected in idea.md §3 that determines default profiles | idea.md §3 |
| **Bounded context** | A domain module in apps/api/app/<context>/ with its own router/models/service | apps/api/app/ |
| **Mandatory skill search** | The required step of searching skills/ before beginning any task | AGENTS.md §13 |
| **Handoff** | The evidence document produced when completing or blocking work | docs/procedures/handoff.md |
| **Ratchet** | A mechanism that only allows coverage floor to increase, never decrease | docs/quality/coverage-policy.md |

## 18.1.3 Domain Model Terms (Placeholder)

Table for project-specific domain terms. Columns: Term, Definition, Module.
Note: This section is populated during initialization from idea.md §4 domain model. Initialization agent fills in entity definitions here.

| Term | Definition | Module |
|------|-----------|--------|
| _(filled during initialization)_ | | |

## 18.1.4 Technical Terms

Table of technical abbreviations and concepts used in code comments and docs. Rows:
- DAG: Directed Acyclic Graph — used in queue intelligence dependency resolution
- DI: Dependency Injection — FastAPI Depends() pattern
- SOP: Standard Operating Procedure — a document in docs/procedures/
- JWT: JSON Web Token — authentication token format used in auth module
- ORM: Object-Relational Mapper — SQLAlchemy in this codebase
- ADR: Architecture Decision Record — in docs/adr/
- RBAC: Role-Based Access Control — permission model
- SBOM: Software Bill of Materials — security artifact for deployed containers
