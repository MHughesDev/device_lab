---
globs:
  - "prompts/**"
description: Rules for prompt files. Ensures prompts have required YAML front matter and follow the metadata convention.
---

# .cursor/rules/prompts.md

Conventions for **`prompts/*.md`**. Full metadata rules live in **`docs/prompts/conventions.md`**. Every template must support **mandatory skill search** (spec §4.1 item 13).

## YAML front matter

1. Each prompt **`.md`** starts with **`---`** delimited YAML.
2. Include at minimum: **`purpose`**, **`when_to_use`**, **`required_inputs`**, **`expected_outputs`**, **`validation_expectations`**, **`constraints`**, **`linked_commands`**, **`linked_procedures`**, **`linked_skills`** (per spec §7.2 — adjust names to match repo conventions documented in **`docs/prompts/README.md`**).
3. **`purpose`**: one clear sentence.
4. **`when_to_use`**: concrete triggers, not vague filler.

## Prompt body

1. Start with a **preamble**: read **[AGENTS.md](../../AGENTS.md)**; run **mandatory skill search**; use **`prompts/skill_searcher.md`** when helpful.
2. Placeholders use **`{{double_braces}}`** consistently.
3. State the **role** ("You are …").
4. Include **numbered steps** for execution.
5. End with a **checkbox validation** list (`- [ ]`).
6. State required **output shape** (markdown sections, file paths, PR fields).

## Linking and index

1. Link at least **one** procedure and **one** skill (or document why generic templates apply).
2. Update **`docs/prompts/index.md`** when adding a template.
3. Deprecated templates: set **`deprecated: true`** and point to replacements.
