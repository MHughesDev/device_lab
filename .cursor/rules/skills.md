---
globs:
  - "skills/**"
description: Rules for skill files. Ensures skills follow the §6.2 structure, include machinery code where applicable, and cross-reference procedures/prompts/rules.
---

# .cursor/rules/skills.md

Structure and linking for **`skills/**/*.md`**. Authoring procedure: **`docs/procedures/update-or-create-skill.md`**. Spec reference: §6.2.

## Required headings

1. Each skill includes: **Purpose**, **When to invoke**, **Prerequisites**, **Relevant files / areas**, **Step-by-step method**, **Command examples**, **Validation checklist**, **Common failure modes**, **Handoff expectations**, **Related procedures**, **Related prompts**, **Related rules**.
2. Stubs may mark body **`TODO`** but headings must exist.
3. Steps are **numbered** and reference real **`make`** targets.
4. Validation sections use **`- [ ]`** checklists.

## Machinery

1. If a **`.py`** accompanies the skill, add a **Machinery** subsection: purpose, how to run, inputs/outputs.
2. Machinery follows **`PYTHON_PROCEDURES.md`** (typing, boundaries, tests where feasible).
3. Wire scripts to **`scripts/README.md`** and the **Makefile** when exposed as commands.

## Cross-references

1. Link at least **one** **`docs/procedures/`** entry.
2. Link **prompts** (or state to use **`prompts/implementation_agent.md`** when generic).
3. List relevant **`.cursor/rules/`** files.
4. Update **`skills/README.md`** when adding discoverable skills.
