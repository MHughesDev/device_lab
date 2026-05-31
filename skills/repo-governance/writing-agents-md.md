# skills/repo-governance/writing-agents-md.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedure: docs/procedures/update-or-create-rule.md -->
<!-- - Spec reference: spec §4 -->

**Purpose:** [FULL SKILL] How to author or update AGENTS.md per §4. Covers all required sections (§4.1 items 1–16), navigation guidance, and machine interface. Per spec §26.4 item 48.

## Purpose

One paragraph. AGENTS.md is the most important file in the repository. It is the default policy surface for all agents. Writing it correctly means every required section has substantive content (not just a heading), the instruction hierarchy is accurate, and all §4.1 sections (including Python procedures and semantic discovery) are present.

## When to Invoke

- When initializing a new repository (updating the mission section with project-specific context)
- When adding a new policy or anti-pattern
- When the instruction hierarchy changes (new scoped AGENTS.md added)
- When a new canonical workflow is established
- After an incident that reveals a missing policy

## Prerequisites

AGENTS.md read completely. Current AGENTS.md read. The change to make is clearly defined.

## Relevant Files/Areas

AGENTS.md (root), apps/api/AGENTS.md, packages/*/AGENTS.md

## Step-by-Step Method

Numbered steps:
1. Read AGENTS.md — memorize all required sections
2. Read the current AGENTS.md completely
3. Identify the section to add/update (which §4.1 item requires change)
4. For section 1 (Mission): write one paragraph per project from IDEA.md §2
5. For section 2 (Hierarchy): ensure all 8 levels listed with correct precedence
6. For section 3 (Workflow): all 12 steps including mandatory skill search
7. For section 13 (Mandatory skill search): the complete 6-step procedure
8. For all other sections: substantive content (not just a heading)
9. For navigation guidance (§4.2): cover repo layout, canonical commands, validation workflow, handoff format
10. Verify no section contradicts another
11. Run `make rules:check` (AGENTS.md is not a rules file but similar validation)
12. PR with rationale

## Command Examples

No specific make targets for AGENTS.md editing, but: `make audit:self` after changes to verify consistency

## Validation Checklist

- [ ] All §4.1 sections present with substantive content
- [ ] Instruction hierarchy table complete and correct (8 levels)
- [ ] Mandatory skill search procedure complete in section 13
- [ ] Navigation section covers: repo layout, canonical commands, validation, handoff format
- [ ] No contradictions between sections
- [ ] Scoped AGENTS.md files (if any) not contradicting root

## Common Failure Modes

- Missing section 13 (mandatory skill search) — agents skip the skill library. Fix: verify it's present with the full 6-step procedure.
- Vague section 1 (Mission) — agents don't understand project context. Fix: fill with project-specific content from IDEA.md §2.

## Handoff Expectations

Updated AGENTS.md committed, no contradictions, all §4.1 sections verified.

## Related Procedures

docs/procedures/update-or-create-rule.md (policy for AGENTS.md updates)

## Related Prompts

prompts/rule_authoring_agent.md

## Related Rules

AGENTS.md itself (the document being updated)
