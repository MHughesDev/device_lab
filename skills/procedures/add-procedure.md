# Add Procedure

Create a new procedure in the repository following canonical structure and sizing guidelines.

## When to invoke

- A workflow has been executed twice and should be encoded
- A gap in procedures is identified during work
- A queue row requires a procedure that doesn't exist
- Refactoring reveals a missing operational workflow

## When NOT to invoke

- One-off tasks (use queue)
- Already-documented workflows (reference existing)
- Simple commands (use skills/README.md listing)
- External best practices (link instead)

## Procedure

### 1. Validate need

**Checklist before proceeding:**
- [ ] Workflow has occurred at least twice (or is critical path)
- [ ] No existing procedure covers this (search `docs/procedures/`)
- [ ] Scope is discrete and bounded (one outcome)
- [ ] Target audience is clear (human, agent, or both)

**Search commands:**
```bash
# Search by keyword
grep -r "your-concept" docs/procedures/ prompts/ skills/

make prompt:list | grep -i "concept"
make skills:list | grep -i "concept"
```

### 2. Determine scope

**Define in writing:**
- **Trigger:** When is this invoked? (e.g., "When adding a new Make target")
- **Outcome:** What specific result? (e.g., "Makefile has new working target")
- **Boundaries:** What is explicitly NOT covered?
- **Duration:** Estimated time to execute (5 min - 2 hours)

**Sizing test:**
- Can you write the outcome in one sentence? If not, split.
- Are there 3-15 steps? If < 3, too small. If > 20, split.

### 3. Assign doc_id

**Section 5 (Procedures) ID ranges:**
- 5.0-5.9: Core (Make, MCP, prompts, queue, db)
- 5.10-5.19: Workflow (archive, handoff, plan, PR, implement)
- 5.20-5.29: Dev (init, scaffold, skills, rules, validation)
- 5.30+: Meta/extended (add-procedure, restructure-docs, etc.)

**Find next available:**
```bash
# Pick next unused number
```

**Format:** `doc_id: "5.NN"` (always 2 digits)

### 4. Create file

**Path:** `docs/procedures/{kebab-case-title}.md`

**Template:**
```markdown
---
doc_id: "5.NN"
title: "kebab-case-title"
section: "Procedures"
status: "draft"
updated: "YYYY-MM-DD"
---

# 5.NN — Title Case Title

**Purpose:** One sentence outcome.

**When to use:** Trigger conditions.

**Prerequisites:** Required state before starting.

---

## Steps

### 1. [Verb] action
details...

### 2. [Verb] action
details...

---

## Validation

How to verify success.

---

## See Also

- Related: `docs/procedures/related.md`
- Skill: `skills/category/skill.md`
```

### 5. Write content

**Section by section:**

**Purpose:** One sentence. Active voice. (e.g., "Add a canonical Make target...")

**When to use:** Bullet list of trigger conditions.

**Prerequisites:** List what must be ready. Use checkboxes if multiple.

**Steps (3-15 total):**
- Each starts with verb (Add, Run, Verify, Update)
- Sequential order (no branching in main flow)
- Show exact commands: `make command` not "run the command"
- Include file paths

**Validation:** Specific verification steps.

**Common Issues (optional):**
| Issue | Cause | Fix |

**See Also:** Cross-references.



Add row to table:
```markdown
| 5.NN | kebab-case-title | `docs/procedures/{filename}.md` | One-line summary. |
```

Keep table sorted by ID.

### 7. Update procedures index

**Edit `docs/procedures/README.md`:**

Add to index list with one-line description.

### 8. Add cross-references

**Where to reference:**
- Parent procedures (that invoke this)
- Related skills (in `skills/`)
- Relevant prompts (in `prompts/`)
- Scoped AGENTS.md files

**How to reference:**
```markdown
## See Also
- Procedure: `docs/procedures/this-one.md`
```

### 9. Validate

**Run checks:**
```bash
```

**Manual check:**
- [ ] 3-15 steps
- [ ] Each step starts with verb
- [ ] Prerequisites clear
- [ ] Cross-references valid
- [ ] doc_id unique

### 10. Handoff

**Include in PR:**
- New procedure file
- Procedures index update
- Cross-reference changes

**PR description:**
```markdown
## New Procedure: {Title} (5.NN)

**Purpose:** {one sentence}
**Sizing:** {N} steps, ~{duration}
**Trigger:** {when to use}

### Files Changed
- `docs/procedures/{file}.md` (new)
- `docs/procedures/README.md` (+1 entry)
- `skills/.../related.md` (+reference)

### Verification
- [ ] Sizing guidelines met
- [ ] Cross-references added
```

## Sizing Guidelines

A well-sized procedure:
- **Outcome:** Single discrete result
- **Steps:** 3-15 (sweet spot: 5-10)
- **Scope:** Bounded with clear boundaries
- **Duration:** 5 min to 2 hours
- **Actors:** 1-2 roles

**Too small (< 3 steps):**
- Merge into related procedure
- Or add to style guide / conventions doc

**Too large (> 20 steps):**
- Extract sub-procedures
- Reference from parent
- Example: "Initialize repo" calls "Setup Python", "Setup DB", "Seed data"

## Examples

### Good (8 steps): `add-make-target.md`
- Clear outcome: target works
- Sequential: check, add, document, test
- Verifiable: run `make target`

### Split candidate (25 steps): "Build application"
- Break into: Setup, Configure, Build, Verify, Deploy
- Each becomes a procedure
- Parent procedure orchestrates

## Machinery (Optional)

If this skill is invoked frequently, consider adding:

**Script:** `skills/procedures/add-procedure.py`
- Interactive prompt for title, scope, steps
- Auto-generates file from template
- Assigns next doc_id

**Usage:**
```bash
python skills/procedures/add-procedure.py
# Interactive prompts...
# Generates: docs/procedures/new-procedure.md
```

## See Also

- Procedure: `docs/procedures/add-procedure.md` (meta)
- Skills: `skills/README.md`
- Prompts: `prompts/README.md`
