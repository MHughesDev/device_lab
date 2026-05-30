---
doc_id: "19.4"
title: "Brainstorm template"
section: "BRAINSTORM"
summary: "Structured template for one whole idea; expect many queue rows and list them in section 10."
updated: "2026-04-20"
---

# 19.4 — Brainstorm template

<!-- Copy this file to ideas/YYYY-MM-DD-<slug>.md and replace angle-bracket placeholders. -->

**One file = one complete idea.** Implementation is **not** one queue row per file by default: add **multiple** `queue/queue.csv` rows and track each ID in **Section 10** below. See [`PIPELINE-from-brainstorm-to-queue.md`](PIPELINE-from-brainstorm-to-queue.md).

## 19.4.1 Metadata

| Field | Value |
|-------|--------|
| **Id** | `BR-<YYYY-MM-DD>-<slug>` (human-readable; optional) |
| **Status** | `draft` \| `review` \| `ready for implementation` \| `in progress` \| `implemented` \| `superseded` |
| **Owner** | `<name or team>` |
| **Created** | `<YYYY-MM-DD>` |
| **Last updated** | `<YYYY-MM-DD>` |
| **Supersedes / superseded by** | `<none or links to other brainstorm files>` |

## 19.4.2 Problem / opportunity

**What is wrong or missing today?** (Facts, pain, constraints.)

-

## 19.4.3 Goal

**What success looks like** in one or two sentences.

-

## 19.4.4 Non-goals

**Explicitly out of scope** so the idea does not sprawl.

-

## 19.4.5 Users and stakeholders

Who is affected (operators, end users, other agents)?

-

## 19.4.6 Proposed direction

**High-level approach** — options considered, preferred option, and why.

### 19.4.6.1 Options considered

| Option | Pros | Cons |
|--------|------|------|
| A | | |
| B | | |

### 19.4.6.2 Preferred approach

-

## 19.4.7 Acceptance criteria (draft)

Bullet list of **testable** outcomes. Refine when moving to queue items.

-

## 19.4.8 Impact and risks

| Area | Risk or impact | Mitigation |
|------|----------------|------------|
| Security / tenancy | | |
| Data / migrations | | |
| API contract | | |
| Ops / rollout | | |

## 19.4.9 Open questions

Numbered list. Resolve before or during implementation.

1. 

## 19.4.10 References

Links to code paths, docs, issues, prior ADRs (optional).

-

## 19.4.11 Implementation tracking (fill when work starts)

**One brainstorm → many queue rows.** Add a row for **each** `queue/queue.csv` item that implements this idea. Put the same brainstorm path in `related_files` on every corresponding queue row.

| Queue ID | Summary (scope of this row) | PR | Notes |
|----------|----------------------------|-----|-------|
| | | | |

## 19.4.12 Changelog (within this brainstorm)

Append-only lines when the idea evolves.

- `<YYYY-MM-DD>` — 
