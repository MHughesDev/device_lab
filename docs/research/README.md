---
doc_id: "23.0"
title: "DeviceLab research workspace"
section: "Research"
summary: "Index for DeviceLab external research: bibliography, queries, notes, and decision tables."
updated: "2026-05-17"
---

# Research workspace

External discovery for **DeviceLab / BYOC cloud device platform** design. This folder keeps queries, skim notes, and bibliographies **separate from** internal architecture docs under `docs/architecture/` and brainstorm materials under `docs/BRAINSTORM/`.

## Folder layout

| Path | Purpose |
|------|---------|
| [**SOURCES.md**](SOURCES.md) | Canonical bibliography: URLs, titles, access dates, one-line takeaways. Use citation IDs like `[S###]` elsewhere. |
| [**open_ended_question.md**](open_ended_question.md) | Decision table: open design questions → recommended answers, confidence, pointers to sources. |
| [**queries/queries-results.md**](queries/queries-results.md) | All web search strings used + compact outcomes (no raw dumps). |
| [**notes/**](notes/) | Domain skim notes written **after** reading search snippets or fetched pages. Aggregates findings; does not mirror third-party docs in full. |
| [**reference/**](reference/) | **Tracked upstream registry** + **direct-read digest** (repos/specs we cite in design). |
| [**external/README.md**](external/README.md) | Policy for linking vs quoting external material (copyright, freshness). |

## How to extend

1. Add a row to `queries-results.md` when running new searches.
2. Add `[S###]` entries to `SOURCES.md` for every URL you rely on.
3. Update `notes/*.md` when synthesis crosses multiple sources.
4. Update `open_ended_question.md` when a decision changes.

## Access dates

Unless noted per entry, batch material was collected **2026-05-17**.
