---
doc_id: "19.3"
title: "Brainstorm idea files"
section: "BRAINSTORM"
summary: "One Markdown file per whole idea; implementation splits into many queue rows via the pipeline."
updated: "2026-04-20"
---

# 19.3 — Brainstorm idea files

**Purpose:** One Markdown file per **whole** brainstorm, using the shared template. That single file is **not** limited to one queue row—when you implement, you add **multiple** rows in `queue/queue.csv` (see [`../PIPELINE-from-brainstorm-to-queue.md`](../PIPELINE-from-brainstorm-to-queue.md) Step 2).

## 19.3.1 Naming

Use:

`YYYY-MM-DD-<short-slug>.md`

Examples:

- `2026-04-20-add-export-api.md`
- `2026-04-21-tenant-audit-log.md`

The date is the **first** time the idea file was created (not updated).

## 19.3.2 How to create

1. Copy [`../TEMPLATE-brainstorm.md`](../TEMPLATE-brainstorm.md).
2. Save under this directory with the naming rule above.
3. Fill all sections; link to related issues, PRs, or **all** queue IDs as they appear (tracking table).

## 19.3.3 Status

Track implementation status **inside** each brainstorm file (template fields). List **every** queue ID that implements part of the idea in the **Implementation tracking** table. Do not rely on filenames alone.
