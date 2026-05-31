# skills/repo-governance/authoring-cursor-rules.md

<!-- CROSS-REFERENCES -->
<!-- - Machinery: skills/repo-governance/rule-linter.py -->
<!-- - Related procedure: docs/procedures/update-or-create-rule.md -->

**Purpose:** [FULL SKILL] How to create or update .cursor/rules/ files. Covers frontmatter, scoping (global vs path), testing enforcement, and avoiding contradictions. Per spec §26.4 item 49.

## Purpose

One paragraph. Cursor rules are machine-enforced constraints. A well-authored rule prevents an entire class of mistakes permanently. Poorly authored rules (vague, contradictory, wrong scope) create confusion. This skill ensures rules are written to the standard that makes them enforceable and audit-ready.

## When to Invoke

- After a repeated agent mistake is identified
- When a new technical constraint needs enforcement (e.g., new import convention)
- When an existing rule is contradicted by a new pattern
- Per AGENTS.md §10 (encoding learning)

## Prerequisites

skills/agent-ops/rule-refinement-after-mistakes.md read. The specific behavior to enforce is clearly defined. All existing rules in .cursor/rules/ have been read.

## Relevant Files/Areas

.cursor/rules/ directory, scripts/rules-check.sh, skills/repo-governance/rule-linter.py

## Step-by-Step Method

Numbered steps:
1. Determine scope: global (alwaysApply: true) or path-scoped (globs: ["pattern/**"])
2. Choose the correct file: create new if new domain, update existing if extending
3. Write YAML frontmatter: alwaysApply or globs + description
4. Write rules as numbered list: "NEVER/MUST/ALWAYS [specific action]"
5. For each rule: add rationale sentence or comment
6. Read ALL other rule files: check for contradictions
7. If extending existing file: add new section with clear heading
8. Run `make rules:check` → `python skills/repo-governance/rule-linter.py`
9. Verify linter passes: frontmatter valid, glob patterns valid, no obvious contradictions
10. PR with rationale linking to the incident that motivated the rule

## Command Examples

`make rules:check`, `python skills/repo-governance/rule-linter.py`

## Validation Checklist

- [ ] Frontmatter present: alwaysApply or globs
- [ ] Description field present in frontmatter
- [ ] Rules are specific (name exact patterns, functions, files)
- [ ] Rules use imperative: NEVER/MUST/ALWAYS
- [ ] No contradictions with other rules (all files read)
- [ ] make rules:check passes
- [ ] rule-linter.py passes

## Common Failure Modes

- Wrong scope: global rule that should be path-scoped → too broad. Fix: use globs for API-specific rules.
- Contradictory rule: "always use async" in global + "sync preferred" in API → confusion. Fix: read all existing rules before writing.

## Handoff Expectations

New rule file committed, rule-linter passes, PR rationale links to motivating incident.

## Related Procedures

docs/procedures/update-or-create-rule.md

## Related Prompts

prompts/rule_authoring_agent.md

## Related Rules

.cursor/rules/skills.md (rules about how rule files should be structured)

## Machinery

`skills/repo-governance/rule-linter.py` — validates rule files for correct frontmatter structure, valid glob patterns, and detects potential contradictions. Run: `python skills/repo-governance/rule-linter.py` or via `make rules:check`.
