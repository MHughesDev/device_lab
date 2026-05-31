# skills/agent-ops/rule-refinement-after-mistakes.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedure: docs/procedures/update-or-create-rule.md -->
<!-- - Related skill: skills/repo-governance/authoring-cursor-rules.md -->

**Purpose:** After a repeated mistake, how to identify the pattern, author or update a .cursor/rules/ entry, and link to the incident. Per spec §26.4 item 45.

## Purpose

One paragraph. Mistakes that happen twice are system failures — not individual agent failures. This skill provides the procedure for encoding observed mistakes into enforceable rules so they cannot happen again. Per AGENTS.md §10 and spec §5.2.

## When to Invoke

After any mistake that has happened ≥2 times. After a PR reviewer identifies a pattern of similar errors. After a post-incident review identifies a preventable failure mode.

## Prerequisites

The mistake has been identified and documented. docs/procedures/update-or-create-rule.md read. skills/repo-governance/authoring-cursor-rules.md read.

## Relevant Files/Areas

.cursor/rules/ directory, docs/repo-governance/improvement-loops.md, scripts/rules-check.sh

## Step-by-Step Method

Numbered steps:
1. Document the mistake pattern: what happened, which file, what the agent did wrong, why
2. Determine the rule type: global constraint (alwaysApply) or path-scoped (globs)
3. Write the rule following authoring-cursor-rules.md: frontmatter + specific numbered rules
4. Check for contradictions against all existing rules (read all files in .cursor/rules/)
5. Run `make rules:check` → run `skills/repo-governance/rule-linter.py`
6. PR with rationale: link to the incident/PR that motivated the rule
7. Announce in AGENTS.md §12 (Anti-patterns) if it's a universal rule

## Command Examples

`make rules:check`, `python skills/repo-governance/rule-linter.py`

## Validation Checklist

- [ ] Rule is specific and actionable (not vague)
- [ ] No contradictions with existing rules
- [ ] make rules:check passes
- [ ] Rule rationale links to incident
- [ ] Rule merged and enforcement verified

## Common Failure Modes

Vague rule ("be careful with security") → unenforceable. Fix: name the specific file, function, or pattern to avoid.

## Handoff Expectations

New rule file PR merged; AGENTS.md updated if universal; incident linked in the rule file or PR description.

## Related Procedures

docs/procedures/update-or-create-rule.md

## Related Prompts

prompts/rule_authoring_agent.md

## Related Rules

.cursor/rules/global.md (all existing global rules to check against)
