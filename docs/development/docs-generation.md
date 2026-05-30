---
doc_id: "3.3"
title: "docs generation"
section: "Development"
summary: "How the deterministic docs-indexing pipeline works, what it generates, and what it explicitly is not."
updated: "2026-05-18"
---

# 3.3 — docs generation

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/development/README.md, README.md -->
<!-- - Helper code: skills/repo-governance/docs-generator.py -->
<!-- - Run: scripts/docs-generate.sh + scripts/docs-check.sh -->

**Purpose:** Explain the deterministic docs-indexing pipeline that produces files under `docs/generated/` from authoritative sources in the repo.

## 3.3.1 What docs-generation is

The docs pipeline is a small, deterministic helper. It reads source artifacts (the `Makefile`, `apps/api/app/core/config.py` Settings, `compose.yml`, `deploy/k8s/base/`, `.cursor/rules/`, `apps/api/app/alembic/versions/`) and writes indexes to `docs/generated/`:

| Output | Source | Purpose |
|---|---|---|
| `docs/generated/make-targets.md` | `Makefile` `## name: description` lines | Table of every Make target. |
| `docs/generated/settings-fields.md` | `apps/api/app/core/config.py` AST | Table of every Settings field with type and default. |
| `docs/generated/compose.md` | `compose.yml` | Service / image / ports / profiles table. |
| `docs/generated/k8s-base.md` | `deploy/k8s/base/` | One block per kind/name. |
| `docs/generated/cursor-rules.md` | `.cursor/rules/` | Rule index with scope and summary. |
| `docs/generated/migrations.md` | `apps/api/app/alembic/versions/` | Alembic revision history. |

The pipeline is driven by [`skills/repo-governance/docs-generator.py`](../../skills/repo-governance/docs-generator.py). It is invoked by `scripts/docs-generate.sh` (regenerate) and checked by `scripts/docs-check.sh` (drift verification in CI).

## 3.3.2 What docs-generation is **not**

- **It is not the product-design brain.** The pipeline does not author architecture, design, API, or operations docs — those are written by a developer or by an AI agent following [`skills/init/repo_initialize.md`](../../skills/init/repo_initialize.md).
- **It does not replace `repo_initialize`.** The source of product intent is [`/idea.md`](../../idea.md). The source of initialization procedure is [`skills/init/repo_initialize.md`](../../skills/init/repo_initialize.md). The outputs of initialization are docs (under `docs/architecture/`, `docs/api/`, `docs/data/`, `docs/security/`, `docs/operations/`, `docs/testing/`) and queue rows.
- **It does not invent content.** Every file under `docs/generated/` is a deterministic projection of an existing source artifact in the repo. Re-running the generator on unchanged sources produces byte-identical output.

## 3.3.3 Commands

| Command | Role |
|---|---|
| `make docs-generate` / `make docs:generate` | Run `scripts/docs-generate.sh` — regenerate every file under `docs/generated/`. |
| `make docs-check` / `make docs:check` | Run `scripts/docs-check.sh` — verify `docs/generated/` matches the current sources (CI fails on drift). |

## 3.3.4 Workflow

1. Change source artifacts (`Makefile` targets, `Settings` fields, `compose.yml`, k8s manifests, cursor rules, alembic revisions).
2. Run `make docs-generate`. Commit the resulting changes under `docs/generated/`.
3. Run `make docs-check` before pushing.
4. CI re-runs `docs-check` on every PR.

## 3.3.5 Extending the pipeline

Adding a new generator means:

- Implementing a new `DocTarget` in `skills/repo-governance/docs-generator.py` (each target is a single function that reads one source and returns a Markdown string).
- Listing the new target in `_default_targets` or `extra` so it runs in both `generate` and `check` modes.
- Ensuring the output path under `docs/generated/` is gitignored or that the file is committed; CI must be able to verify drift.

Generators must be deterministic, side-effect-free, and stateless. Anything that requires judgment belongs in a skill, not the docs pipeline.

## 3.3.6 Related

- [skills/repo-governance/docs-generator.md](../../skills/repo-governance/docs-generator.md) — skill that wraps the helper.
- [skills/init/repo_initialize.md](../../skills/init/repo_initialize.md) — canonical initialization procedure; produces design docs, not generated docs.
- [docs/api/endpoints.md](../api/endpoints.md) — endpoint catalog (regenerate when routes change).
