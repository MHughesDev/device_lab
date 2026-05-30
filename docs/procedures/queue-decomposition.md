---
doc_id: "5.28"
title: "queue decomposition"
section: "Procedures"
summary: "Break L-complexity queue tasks into S/M sub-tasks that satisfy touch file and dependency constraints."
updated: "2026-05-16"
---

# Procedure: Decomposing L-Complexity Queue Items

**Purpose:** SOP for breaking an oversized (L-complexity) task into S/M
sub-tasks that can be processed by a constrained-context agent.
**When to use:** When planning work that would produce a queue row with
more than 3 touch_files, or when any split trigger fires.
**Per:** `queue/QUEUE_INSTRUCTIONS.md` — Granularity Rules section.

---

## Step 1 — Identify the parent scope

Write down in plain English what the full L-task was trying to accomplish.
This becomes your decomposition target. The parent ID (e.g. Q-042) is
**never** added to the queue — it exists only as a label for the set.

## Step 2 — Apply the split triggers

Read `queue/QUEUE_SPLIT_TRIGGERS.md`. For each trigger that fires, mark a
split point. Common patterns:

- **Interface then implementation:** Define the contract (interface, schema,
  type) as S-task a. Implement against it as S/M-task b.
- **Implementation then tests:** Implement as task a. Write tests as task b
  with dependency on a.
- **Dependency then consumer:** Add new package as S-task a
  (touch: manifest + lock). Wire the consumer as task b.
- **Feature then localization:** Build feature as M-task a. Add i18n strings
  as S-task b.
- **Feature then docs:** Implement as task a. Update spec/docs as S-task b.

## Step 3 — Write the sub-task rows

For each sub-task:
- Assign ID: `Q-NNNa`, `Q-NNNb`, etc.
- Fill ALL required columns: `complexity`, `goal`, `acceptance_criteria`,
  `touch_files`, `context_files`
- Set `dependencies` to chain: b depends on a, c depends on b
- Keep `goal` to 1–2 sentences
- Keep `acceptance_criteria` verifiable and numbered
- Keep `touch_files` within the complexity limit

## Step 4 — Validate before inserting

Run the Pre-Flight Split Check from `queue/QUEUE_AGENT_PROMPT.md` against
each sub-task row mentally before inserting. If any row still fails, split
further.

## Step 5 — Insert in dependency order

Insert sub-tasks into `queue.csv` in dependency order: Q-NNNa first,
Q-NNNb after. Run `make queue:validate` after insertion. Fix any failures.

## Step 6 — Document in CHANGELOG

Add an entry to `CHANGELOG.md` noting the decomposition:
`Decomposed Q-NNN into Q-NNNa, Q-NNNb, ... (granularity requirement)`

---

## Anti-patterns to avoid

- Do NOT write a sub-task that still has more touch_files than its complexity
  allows. Split again.
- Do NOT merge two sub-tasks into one to "save rows." Each row = one commit.
- Do NOT leave `touch_files` empty on any sub-task. If you can't enumerate
  the files, the task isn't ready to be written.
- Do NOT chain more than 4 sub-tasks without checking if the parent scope
  was correct. More than 4 usually means the original feature is too large
  for one sprint/session.
