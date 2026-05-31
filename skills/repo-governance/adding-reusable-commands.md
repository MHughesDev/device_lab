# skills/repo-governance/adding-reusable-commands.md

<!-- CROSS-REFERENCES -->
<!-- - Related procedure: docs/procedures/implement-change.md -->

**Purpose:** How to add entries to .cursor/commands/ or Makefile targets. Ensure no duplication, document in README and local-setup.md. Per spec §26.4 item 50.

## Purpose

One paragraph. Canonical commands reduce the chance of agents using wrong or inconsistent approaches. Every recurring multi-step operation deserves a named Make target or Cursor command. This skill ensures new commands are added consistently.

## When to Invoke

When a recurring multi-step operation is identified that doesn't have a Make target. When adding a new Cursor command for an initialization or scaffolding workflow. When a script is written that should be exposed as a canonical target.

## Prerequisites

The operation is clearly defined. A script in scripts/ exists or will be created. Makefile and docs/development/local-setup.md read.

## Relevant Files/Areas

Makefile, scripts/README.md, docs/development/local-setup.md, .cursor/commands/, README.md

## Step-by-Step Method

Numbered steps:
1. Verify the operation doesn't already have a Make target (read Makefile completely)
2. For Makefile target: add to Makefile with ## help comment, .PHONY declaration, delegate to script
3. For Cursor command: create .cursor/commands/<name>.md with metadata, steps, expected output
4. Create or update the backing script in scripts/ if needed
5. Update scripts/README.md with the new script
6. Update docs/development/local-setup.md with the new target
7. Update README.md Key Commands table if it's a primary command
8. Run `make help` to verify the new target appears

## Command Examples

`make help` (verify target appears)

## Validation Checklist

- [ ] No duplicate target exists
- [ ] .PHONY declaration added to Makefile
- [ ] ## help comment present
- [ ] Backing script executable (chmod +x scripts/*.sh)
- [ ] docs/development/local-setup.md updated
- [ ] make help shows the new target

## Common Failure Modes

Duplicate target with different behavior → confusion. Fix: always read the full Makefile before adding.

## Handoff Expectations

New target documented, help text accurate, script tested.

## Related Procedures

docs/procedures/implement-change.md

## Related Prompts

prompts/implementation_agent.md

## Related Rules

.cursor/rules/global.md (canonical commands — ad hoc shell is disfavored)
