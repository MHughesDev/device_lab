---
globs:
  - "IDEA.md"
  - "prompts/repo_initializer.md"
  - "skills/init/*.md"
description: Guardrails for the AI-driven, documentation-first repo initialization flow.
---

# .cursor/rules/initialization.md

## Required behavior

1. Treat `IDEA.md` as the **single** human-authored input contract for initialization. A developer fills it out end-to-end before invoking the AI.
2. After `IDEA.md` is filled out, run **`skills/init/repo_initialize.md`** — this is the canonical procedural skill for initialization. There is no `make idea:*` target.
3. Initialization is documentation-first and queue-first: refresh the spec, derive design docs under `docs/`, then seed `queue/queue.csv` from those docs. Do not write product code from initialization.
4. Treat ambiguity in `IDEA.md` as a first-class output: create blocked `category=human-ops` queue rows or `docs/open-questions.md` entries. Do not silently invent product decisions.

## Prohibited

- Do not modify files under `apps/api/app/` or `apps/web/src/` as part of initialization — application work is queued, not initialized.
- Do not execute legacy commands or scripts (`make idea:validate`, `make idea:execute`, `scripts/validate-idea.sh`, `scripts/init-from-idea.py`, `scripts/idea-parser.py`, `init-manifest.json`). These have been removed.
- Do not re-introduce the multi-skill init pipeline (archetype-mapper / profile-resolver / queue-seeder / idea-validator). The single `repo_initialize` skill replaces it.
