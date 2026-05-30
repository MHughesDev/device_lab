---
doc_id: "5.29"
title: "template upgrade"
section: "Procedures"
summary: "Manual upgrade path for projects initialized from this template."
updated: "2026-05-16"
---

# 5.22 — template upgrade

## Purpose
Apply improvements from newer template versions into existing initialized repositories.

## Steps
1. Compare your `idea.md` `init_version` and `template_version` to upstream.
2. Review changes in `AGENTS.md`, `skills/`, `prompts/`, `docs/procedures/`, `Makefile`.
3. Cherry-pick or manually port compatible workflow/docs changes.
4. Run: `make docs:check`, `make queue:validate`, `make lint`, `make typecheck`, `make test`.
5. Record upgrade notes in PR and `CHANGELOG.md`.
