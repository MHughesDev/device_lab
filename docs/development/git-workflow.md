---
doc_id: "3.5"
title: "git workflow"
section: "Development"
summary: "Git branching, PR workflow, and review expectations for this repository."
updated: "2026-04-17"
---

# 3.5 — git workflow

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/development/README.md, README.md -->

**Purpose:** Git branching, PR workflow, and review expectations for this repository.

## 3.5.1 Overview

Git branching, PR workflow, and review expectations for this repository. See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

## 3.5.2 Branches

| Pattern | Use |
|---------|-----|
| `queue/<id>-short-slug` | Queue-driven work; include the queue item ID |
| `cursor/<descriptive-slug>-<suffix>` | Agent work not tied to a queue row |

Do not push directly to `main`; changes land via pull request.

## 3.5.3 Pull requests

- One logical change per PR when possible.
- Use `.github/PULL_REQUEST_TEMPLATE.md` for the description.
- Include evidence: commands run (`make lint`, `make test`, etc.), files changed, risks.
- CI must be green before merge.

## 3.5.4 Local workflow

1. Branch from an up-to-date `main`.
2. Commit in small, reviewable steps.
3. Before opening or updating a PR: `make lint`, `make fmt`, `make typecheck`, `make test`.
4. If you touched `queue/` files: `make queue-validate` / `make queue:validate`.

## 3.5.5 Related

- [open-pull-request.md](../procedures/open-pull-request.md)
- [AGENTS.md](../../AGENTS.md) section 4 (branch and PR policy)
