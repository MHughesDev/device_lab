# skills/agent-ops/prompt-to-procedure-promotion.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedure: docs/procedures/add-prompt-template.md -->
<!-- - Related rule: .cursor/rules/prompts.md -->

**Purpose:** When and how to promote a successful one-off prompt into prompts/ with full metadata. Per spec §26.4 item 44.

## Purpose

One paragraph. Successful one-off prompts should become library templates so the knowledge is reusable and not lost. This skill defines when a prompt is worth promoting and how to do it correctly per §7.2 metadata standards.

## When to Invoke

When a one-off prompt has been used successfully 2+ times for the same type of task. When the prompt produces consistent, high-quality results that would benefit other agents. When AGENTS.md §10 says to encode recurring patterns.

## Prerequisites

The one-off prompt exists and its outputs were verified good. Related procedures and skills identified. Understanding of §7.2 metadata format.

## Relevant Files/Areas

prompts/ directory, docs/procedures/add-prompt-template.md, docs/prompts/index.md, .cursor/rules/prompts.md

## Step-by-Step Method

Numbered steps:
1. Verify the prompt has been used successfully ≥2 times (document the instances)
2. Create prompts/<snake_case_name>.md with YAML front matter (all §7.2 fields)
3. Write prompt body: role definition, skill search preamble, steps, output format, validation checklist
4. Link to all related procedures and skills
5. Update docs/prompts/index.md with new entry
6. Update prompts/README.md table
7. Run make prompt:list to verify it appears
8. PR with evidence: examples of successful uses

## Command Examples

`make prompt:list`, `make rules:check`

## Validation Checklist

- [ ] YAML front matter has all §7.2 fields
- [ ] Prompt body has preamble (mandatory skill search reference)
- [ ] Validation checklist included in prompt body
- [ ] docs/prompts/index.md updated
- [ ] make prompt:list shows new template
- [ ] Related skills and procedures linked

## Common Failure Modes

Missing front matter fields → make rules:check fails. Fix: check all §7.2 fields against .cursor/rules/prompts.md.

## Handoff Expectations

New prompt file committed, indexes updated, PR description documents the instances where the one-off prompt succeeded.

## Related Procedures

docs/procedures/add-prompt-template.md

## Related Prompts

prompts/skill_authoring_agent.md

## Related Rules

.cursor/rules/prompts.md
