---
doc_id: "5.23"
title: "update or create rule"
section: "Procedures"
summary: "SOP: Rule lifecycle — creating new .cursor/rules or updating existing ones."
updated: "2026-04-17"
---

# 5.23 — update or create rule

<!-- CROSS-REFERENCES -->
<!-- - Skill: skills/agent-ops/rule-refinement-after-mistakes.md -->
<!-- - Skill: skills/repo-governance/authoring-cursor-rules.md -->

**Purpose:** SOP: Rule lifecycle — creating new .cursor/rules or updating existing ones. Per spec §26.5 item 149 and §8.3.

## 5.23.1 Purpose

Rules prevent recurrence of known failure modes. Adding them correctly ensures they are enforceable, auditable, and non-contradictory.

## 5.23.2 Trigger / When to Use

After a repeated mistake is identified. When a new constraint needs encoding. Per AGENTS.md §10 policy.

## 5.23.3 Prerequisites

Specific behavior to prevent is clearly defined. All existing .cursor/rules files read.

## 5.23.4 Exact Commands

`make rules:check`, `python skills/repo-governance/rule-linter.py`

## 5.23.5 Ordered Steps

1. Identify the specific pattern/mistake (link to the PR or incident)
2. Determine scope: global (alwaysApply) or path-scoped (globs)
3. Choose existing file to update OR create new .cursor/rules/<name>.md
4. Write YAML frontmatter: alwaysApply or globs, description
5. Write rule(s) as numbered list with NEVER/MUST/ALWAYS + specific pattern
6. Read ALL other rule files: check for contradictions
7. Run `make rules:check`
8. Run `python skills/repo-governance/rule-linter.py` — verify no findings
9. PR with rationale linking to the incident/pattern

## 5.23.6 Expected Artifacts / Outputs

New or updated rule file. make rules:check passing.

## 5.23.7 Validation Checks

- [ ] Rule is specific and actionable
- [ ] No contradictions with other rules
- [ ] make rules:check passes
- [ ] Rationale links to incident

## 5.23.8 Rollback or Failure Handling

If rule causes lint errors in legitimate code: rule is too broad. Narrow the scope with globs.

## 5.23.9 Handoff Expectations

Rule committed, enforcement verified, PR links to motivating incident.
