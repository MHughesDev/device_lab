---
doc_id: "5.22"
title: "update documentation"
section: "Procedures"
summary: "SOP: When and how to update docs alongside code changes."
updated: "2026-04-17"
---

# 5.22 — update documentation

<!-- CROSS-REFERENCES -->
<!-- - Rule: .cursor/rules/documentation.md -->
<!-- - Skill: skills/repo-governance/maintaining-procedural-docs.md -->

**Purpose:** SOP: When and how to update docs alongside code changes. Per spec §26.5 item 147 and §8.3.

## 5.22.1 Purpose

Documentation updated alongside the code change it describes keeps the system self-consistent. Deferred documentation updates always drift.

## 5.22.2 Trigger / When to Use

Per .cursor/rules/documentation.md triggers: new env var, new endpoint, behavior change, ops change, new error code, architectural decision.

## 5.22.3 Prerequisites

Code change implemented. Affected docs identified.

## 5.22.4 Exact Commands

`make docs:check`, `make docs:generate`, `make docs:index`

## 5.22.5 Ordered Steps

1. Identify all affected docs using .cursor/rules/documentation.md trigger list
2. For generated docs (endpoints.md, environment-vars.md, error-codes.md): update the source, then `make docs:generate`
3. For manual docs: edit the specific sections that changed
4. Update doc indexes if new files were added
5. Run `make docs:check` — verify no broken links
6. For generated docs: verify make docs:check shows no drift
7. Commit docs changes alongside the code change (same PR or immediate follow-up)

## 5.22.6 Expected Artifacts / Outputs

Updated documentation files. make docs:check passing.

## 5.22.7 Validation Checks

- [ ] All trigger conditions checked
- [ ] Generated docs regenerated via make docs:generate
- [ ] Manual docs updated with specific changed sections
- [ ] make docs:check passes

## 5.22.8 Rollback or Failure Handling

If make docs:check fails on broken links: fix the link or the referenced file.

## 5.22.9 Handoff Expectations

Docs updated, check passing, docs changes in same PR as code changes.
