---
doc_id: "23.11"
title: "Research reference — tracked external sources"
section: "Research"
summary: "Index of canonical repos and docs URLs DeviceLab design pulls from; links to skim digest."
updated: "2026-05-17"
---

# Reference workspace (`docs/research/reference/`)

This folder tracks **canonical upstream URLs and repositories** we rely on for DeviceLab architecture — separate from web-search logs in [`../queries/`](../queries/).

| File | Purpose |
|------|---------|
| **[`EXTERNAL_REFERENCE.md`](EXTERNAL_REFERENCE.md)** | **Part A:** Registry (slug, URL, license notes). **Part B:** Skim digest from direct HTTP/GitHub raw reads (no full doc mirrors). |

## How to use

1. Add a row to **Part A** before depending on a new upstream in specs or code.
2. After reading a page or README, append bullets under **Part B** (or dated subsection) with **retrieve date** and **URL**.
3. Prefer linking to official docs; use `raw.githubusercontent.com` only for immutable README snapshots when summarizing.

## What we do **not** store here

- Full copies of vendor documentation (copyright).
- Vendored upstream source trees — clone separately if you need offline archives.

See also [`../external/README.md`](../external/README.md).
