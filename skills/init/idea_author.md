# skills/init/idea_author.md

**Purpose:** Help a developer (or an AI agent acting on their behalf) turn raw product input — existing notes, a PRD, a sketch, prior conversation, or a single free-form prompt — into a **completely filled-out `IDEA.md`** that conforms to the intake contract. The skill **replaces** the blank-but-structured stub at the repo root with a real, product-specific document, ready for [`skills/init/repo_initialize.md`](repo_initialize.md) to consume.

This skill is the **upstream** step in the initialization flow:

```
raw materials  ─►  skills/init/idea_author.md  ─►  filled IDEA.md
                                                       │
                                                       ▼
                                              skills/init/repo_initialize.md
                                                       │
                                                       ▼
                                              refreshed spec + docs + initial MVP queue rows
```

> **Hard rule:** this skill does not run `repo_initialize`. It produces (or completes) `IDEA.md` and stops. The developer reviews `IDEA.md`, edits if needed, then explicitly asks an agent to run `repo_initialize`.

---

## When to invoke

- A developer wants to start a new product but has not written `IDEA.md` yet. They have one of:
  - a free-form prompt describing the product,
  - one or more existing documents (PRD, brief, design notes, brainstorm, slack thread, sketch),
  - a partial fill of `IDEA.md` with some sections done and others blank.
- The current `IDEA.md` is the **template stub** (every applicable section blank) or a partially filled draft that needs to be completed.
- The developer explicitly asks for help writing `IDEA.md` (e.g. "draft an IDEA.md from these notes", "fill out IDEA.md based on this PRD", "I have a one-liner — turn it into a full IDEA.md").

Do **not** invoke when:

- `IDEA.md` is already filled out end-to-end and the developer has asked for initialization. Skip directly to `skills/init/repo_initialize.md`.
- The developer has not provided any source material and refuses to answer clarifying questions. Without input, this skill produces a row of unanswered questions, not an IDEA.md. Stop and ask.
- The product has already been initialized (the spec and queue reflect a product). Editing `IDEA.md` after initialization is allowed, but it does not re-trigger this skill — use the standard docs/queue procedures.

---

## Prerequisites

- The root [`IDEA.md`](../../IDEA.md) exists. (If a previous initialization is in progress, do not destructively overwrite — see "Detect prior content" below.)
- Source material is available: a user prompt in the current conversation, file paths the user has pointed at, or visible attached documents. If only a one-liner exists, you can proceed but expect to ask many clarifying questions.
- You have read root [`AGENTS.md`](../../AGENTS.md), [`docs/adr/0001-initial-template-architecture.md`](../../docs/adr/0001-initial-template-architecture.md) (so you understand what `IDEA.md` is for), and the current `IDEA.md` template itself (so you know the 20 canonical sections).
- You can write to the repo root and have permission to open a PR with the edited `IDEA.md`.

---

## What this skill does NOT do

- Does not refresh design docs or queue rows. That is `skills/init/repo_initialize.md`'s job.
- Does not write product feature code under `apps/api/app/` or `apps/web/src/`.
- Does not invent product decisions when the input is silent. Anything the input doesn't cover is either marked `N/A` (with a one-line reason) or recorded in §19 "Open questions" — never silently chosen.
- Does not delete or rewrite sections the developer has already filled out. Existing answers are preserved verbatim unless the developer explicitly asks for a rewrite.
- Does not remove sections from `IDEA.md`. The 20-section schema is canonical.

---

## Inputs the skill accepts

| Input type | Examples | Treatment |
|---|---|---|
| **Free-form prompt** | "Build a B2B invoicing app where vendors send invoices and customers approve them in a dashboard." | Treat as the primary statement of intent. Decompose across sections §1–§7 and §10–§13. Ask follow-ups for anything missing. |
| **Existing document(s)** | PRD, design brief, market research, brainstorm doc, Slack export, README of a related project, recorded transcript. | Read end-to-end first. Quote-and-attribute when content maps cleanly to a section. Note disagreements between documents in §19. |
| **Partial IDEA.md** | Some sections filled, others blank. | Preserve filled sections verbatim. Use them as context when filling the blank sections (e.g. §4 MVP must be consistent with §3 problem). |
| **Sketch / screenshot / wireframe** | UI mockup, ER diagram. | Translate into §7 workflows or §8 entities. Note in §20 "Additional context" that the source was a visual artifact and link or describe it. |
| **One-liner** | "An app like X but for Y." | Acceptable, but you will need to ask the developer many clarifying questions before §4 MVP can be filled. Do not invent a product from a one-liner. |

---

## Procedure

### Phase 0 — Detect prior content

1. Read the current `IDEA.md` end-to-end.
2. For each section, classify:
   - **Stub** — the template's placeholder content, no real product information yet.
   - **Filled** — has real, product-specific content (the developer or a prior agent already wrote it).
   - **Mixed** — partially filled (e.g. only one of the table cells is real).
3. If **every** applicable section is already filled and the developer did not explicitly ask for a rewrite, stop and tell them `IDEA.md` already looks complete — they probably want `repo_initialize`, not this skill.
4. If **filled** sections exist alongside stubs, plan to **preserve** the filled content and only complete the stubs. Do not overwrite filled sections without explicit permission.

### Phase 1 — Read inputs

1. Read every source document the developer provided. Note the path or attachment name beside each quote you intend to reuse.
2. Build a private mapping (do not write to disk yet) from input content to IDEA.md sections:
   - §1 Product identity ← name, slug, one-liner from the prompt/PRD header.
   - §2 Target users ← roles named in the source.
   - §3 Core problem ← any "Problem" / "Why" section.
   - §4 MVP scope ← acceptance bullets, "minimum lovable", "v1 must do".
   - §5 Out of scope ← "Not in v1", "post-MVP", explicit non-goals.
   - §6 User stories ← any "As a … I want …" lines.
   - §7 Workflows ← user journeys, flow diagrams, step lists.
   - §8 Data and entities ← entity names, schemas, ER diagrams.
   - §9 Integrations ← named third-party systems.
   - §10 Auth/permissions ← roles, access rules, SSO mentions.
   - §11 Frontend expectations ← page/screen lists, design refs.
   - §12 Backend/API expectations ← API style, key endpoints.
   - §13 Deployment expectations ← hosting, cloud provider, domain.
   - §14 Security/privacy ← compliance mentions, PII categories.
   - §15 Testing expectations ← QA process, coverage targets.
   - §16 Acceptance criteria ← "Done when …" statements.
   - §17 NFRs ← performance, scale, availability targets.
   - §18 Hard constraints ← mandates ("must run on Python 3.12", "must be self-hosted").
   - §19 Open questions ← TODOs, "TBD", explicit questions.
   - §20 Additional context ← links and references.

### Phase 2 — Surface gaps before writing

Before writing anything to disk, list the gaps:

- For each section where the input is silent, note whether it is plausibly `N/A` for this product (e.g. a B2B internal tool may have no mobile expectations) or whether the developer needs to answer.
- For each section where multiple input documents disagree, list the conflict so the developer can resolve it.
- For the **MVP bullets (§4)** specifically: if you cannot list 3–7 testable, user-visible capabilities from the input, **stop** and ask. The MVP is the most important part of the document; do not guess.

Present this list to the developer (in chat) and ask them to:

- Answer the questions you cannot answer from the input, or
- Confirm that an item should be marked `N/A` with a one-line reason, or
- Approve recording an item in §19 "Open questions" instead of answering now.

Only proceed to Phase 3 after the developer responds. If they say "use your best judgment for the rest," do not invent — mark every remaining gap as an open question.

### Phase 3 — Write `IDEA.md`

1. For each section, fill the content according to the mapping built in Phase 1 and the answers gathered in Phase 2.
2. Preserve the section numbering and headings exactly as they appear in the current template. Do not add or remove sections.
3. Where the developer gave you verbatim text that fits a section, quote it. Where you summarized or rephrased, do so faithfully — do not embellish.
4. For each section that is genuinely inapplicable to this product, write `N/A — <one-line reason>`. Do not leave the section blank.
5. For each unresolved gap, add a numbered entry in §19 "Open questions" describing the question, the section(s) it affects, and (if applicable) the candidate answers under consideration.
6. In §20 "Additional context", record the source materials you used (file names, links, prompt excerpts) so future readers can trace any claim back to its origin.

### Phase 4 — Self-check before handing off

Run this checklist over the file you just wrote:

- [ ] Every section is present in the original template order.
- [ ] No section is blank — each is either filled, marked `N/A — <reason>`, or has an entry in §19 covering it.
- [ ] §4 MVP scope contains 3–7 user-visible, independently-testable bullets ordered by dependency.
- [ ] §5 Non-goals is non-empty (every product has at least one explicit non-goal).
- [ ] §6 stories and §7 workflows are consistent with §4 (each MVP bullet has at least one story or workflow).
- [ ] §8 entities cover every noun named in §7 workflows.
- [ ] §10 auth model is consistent with §2 user roles.
- [ ] §16 acceptance criteria are testable (a reviewer can confirm pass/fail without reading code).
- [ ] §19 lists every unresolved question raised in Phase 2.
- [ ] §20 lists the sources used so the developer can audit your work.

If any check fails, fix it before handing off.

### Phase 5 — Handoff

Produce a short handoff message that contains:

- A summary of which sections were newly written vs preserved from prior content.
- A bulleted list of `§19` open questions the developer still owes answers to (these will become blocked `category=human-ops` queue rows when `repo_initialize` runs).
- A reminder that the **next step** is to review `IDEA.md`, fix anything wrong, and **then** ask an agent to run [`skills/init/repo_initialize.md`](repo_initialize.md). Do not initialize from this skill.
- Do not auto-merge. If you opened a PR, title it `idea: <product name>` so it's distinct from later `init:` and feature PRs.

---

## Helper prompts (optional, called mid-procedure)

Use these prompts when a specific section is hard to fill from the source material alone:

- [`prompts/domain_modeler.md`](../../prompts/domain_modeler.md) — when §8 entities are vague and you need a structured way to elicit them from the developer.
- [`prompts/task_planner.md`](../../prompts/task_planner.md) — when §4 MVP scope needs to be decomposed into dependency-ordered bullets.
- [`prompts/skill_searcher.md`](../../prompts/skill_searcher.md) — to find domain-specific skills (e.g. billing, multi-tenancy, AI/RAG) that may surface considerations the developer should record in `IDEA.md`.

These are **prompts**, not sub-skills: invoke them inline when you reach the relevant phase, then return to this procedure.

---

## Acceptance criteria

Authoring is **not complete** until every item is true:

1. `IDEA.md` at the repo root has all 20 sections present, in order, with no section left blank.
2. Every section is filled with product-specific content, marked `N/A — <reason>`, or covered by a §19 open question.
3. No section's content was invented without source-material backing or developer confirmation.
4. §4 MVP scope contains between 3 and 7 user-visible, testable bullets ordered by dependency.
5. §19 lists every unresolved question raised in Phase 2 (questions, not assumptions).
6. §20 lists the source materials the skill consumed.
7. No edits were made under `apps/api/app/`, `apps/web/src/`, `spec/`, `docs/architecture/`, `docs/api/`, `docs/data/`, `docs/security/`, `docs/operations/`, `docs/testing/`, or `queue/`. This skill writes **only** to `IDEA.md`.
8. The developer has been told the next step is to review and then invoke `skills/init/repo_initialize.md`.

---

## Cross-references

- Output of this skill: [`/IDEA.md`](../../IDEA.md)
- Downstream skill: [`skills/init/repo_initialize.md`](repo_initialize.md)
- Invocation prompt for the downstream step: [`prompts/repo_initializer.md`](../../prompts/repo_initializer.md)
- Founding ADR: [`docs/adr/0001-initial-template-architecture.md`](../../docs/adr/0001-initial-template-architecture.md)
- Helper prompts: [`prompts/domain_modeler.md`](../../prompts/domain_modeler.md), [`prompts/task_planner.md`](../../prompts/task_planner.md), [`prompts/skill_searcher.md`](../../prompts/skill_searcher.md)
