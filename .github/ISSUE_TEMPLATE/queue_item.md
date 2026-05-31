---
name: Queue Item
description: Structured issue ready for queue.csv import
labels: ["type:queue"]
---
<!-- .github/ISSUE_TEMPLATE/queue_item.md -->
<!-- Per spec §26.7 item 201 -->

## Summary (Elaborative — ≥100 chars required)

Elaborate summary following the queue contract: goal, acceptance criteria, definition of done, out-of-scope, dependencies. This text goes directly into queue.csv summary column.

**Goal:**
<!-- What must be accomplished -->

**Acceptance criteria:**
<!-- How to verify the work is complete (measurable) -->

**Definition of done:**
<!-- What "complete" looks like: tests passing, docs updated, queue archived -->

**Out of scope:**
<!-- What this queue item explicitly does NOT cover -->

**Dependencies:**
<!-- Other queue IDs that must be done before this one (or "none") -->

## Category

Select from docs/queue/queue-categories.md

- [ ] core-api
- [ ] infrastructure
- [ ] testing
- [ ] documentation
- [ ] bugfix
- [ ] refactor
- [ ] security
- [ ] devops

## Priority

Where in the queue should this item appear?

- [ ] High (top of queue — next item to process)
- [ ] Normal (add after current in-progress batch)
- [ ] Low (add after existing open items)
