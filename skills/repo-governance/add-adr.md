# skills/repo-governance/add-adr.md

<!-- CROSS-REFERENCES -->
<!-- - Template: docs/adr/template.md -->
<!-- - Index: docs/adr/README.md -->
<!-- - Index generator: skills/repo-governance/adr-index-generator.py -->
<!-- - Format variants: skills/repo-governance/references/adr-templates.md -->
<!-- - Architecture methodology: skills/repo-governance/architecture-design.md -->
<!-- - Supersedes: skills/repo-governance/writing-adrs.md -->
<!-- - Rule: .cursor/rules/documentation.md (ADRs for significant architecture) -->
<!-- - Rule: .cursor/rules/global.md (architectural decisions need ADR + PR link) -->
<!-- - Policy: AGENTS.md §8 -->

**Purpose:** Create a well-formed Architecture Decision Record in `docs/adr/` whenever a significant architectural choice is made, a constraint is accepted, or a prior decision is superseded. Follows the Nygard foundation extended with alternatives table and references — the format already established in this repo.

---

## When to Invoke

Invoke this skill before merging any PR that contains one of the following:

- Choosing a framework, library, or external service
- Selecting a database, storage backend, or message broker
- Defining an auth strategy, tenancy model, or security pattern
- Accepting a significant constraint from `IDEA.md` §13
- Deprecating or replacing an existing architectural pattern
- Making a data model decision that affects more than one bounded context
- Any decision that, if reversed later, would require significant rework

**Do NOT create an ADR for:**
- Implementation details within a single bounded context
- Bug fixes
- Refactoring that does not change observable behavior or interfaces
- Queue item scope decisions (those belong in queue notes)

**Policy:** `.cursor/rules/global.md` requires every architectural decision to include both an ADR and a link to it in the PR description. This is non-negotiable.

---

## Prerequisites

- The decision has been made — ADRs record settled decisions, not open debates
- `docs/adr/README.md` read to determine the next sequential number
- `docs/adr/template.md` read (the base template)
- Rationale is clear and at least two alternatives were genuinely considered

---

## Format Selection

This repo uses the **extended Nygard format** as its default. Choose the variant based on the decision type:

| Decision type | Format to use |
|---|---|
| Standard architectural choice | Extended Nygard (default — use this repo's template) |
| Many options with detailed trade-off comparison | MADR variant: add a **Decision Drivers** section and expand Alternatives into a full Pros/Cons table per option |
| Significant business/cost implications | Business Case variant: add **Evaluation Criteria** and **Cost Analysis** subsections under Alternatives |
| Replacing or deprecating a prior ADR | Standard, but add `**Supersedes:** ADR-NNN` line under Status |
| Founding/initial architecture | Use the structure already in `docs/adr/0001-initial-architecture.md` — one Decision block per topic area |

When in doubt, use the default extended Nygard. A thinner ADR that gets written is better than a comprehensive one that doesn't.

---

## The Full Template

Every ADR in this repo follows this exact structure. Copy it, do not paraphrase it.

```markdown
---
doc_id: "7.N"
title: "ADR-NNN kebab case title"
section: "ADR"
summary: "One sentence: status + decision made."
updated: "YYYY-MM-DD"
---

# 7.N — ADR-NNN: Decision Title

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-NNN

**Date:** YYYY-MM-DD

## 7.N.1 Context

What situation or problem prompted this decision? Include:
- The system state that made a decision necessary
- Constraints or forces at play (technical, organizational, timeline)
- Why this had to be decided now rather than deferred

## 7.N.2 Decision

What was decided? Be specific and concrete. State the exact approach — not "we will consider X" but "we will use X for Y because Z."

## 7.N.3 Consequences

What changes as a result of this decision?

**Easier:** What becomes simpler, faster, or lower-risk.

**Harder:** What becomes more complex, constrained, or expensive.

**Risks accepted:** Residual risks that are not mitigated by the decision.

**Follow-up work:** Queue items or future decisions this decision defers or creates.

## 7.N.4 Alternatives Considered

Minimum two alternatives. More is better. Be honest about why each was rejected.

| Alternative | Rejected because |
|---|---|
| Option A | Specific reason with trade-off |
| Option B | Specific reason with trade-off |

## 7.N.5 References

- Links to relevant code files or modules
- Links to prior ADRs that informed this one
- Links to `docs/architecture/` documents affected by this decision
- External documentation, benchmarks, or articles that supported the decision
- `queue/queue.csv` row IDs if implementation work is tracked there
```

---

## Step-by-Step Method

### Step 1 — Determine the next ADR number

```bash
cat docs/adr/README.md
```

Find the highest `ADR-NNN` number in the index. Increment by one. Zero-pad to three digits: `001`, `002`, `013`, `042`.

### Step 2 — Determine the doc_id

The `doc_id` follows the pattern `7.N` where N is the position of this ADR in the `docs/adr/` directory listing. Count existing ADR files (excluding `README.md` and `template.md`) and add one. Example: if 3 ADRs exist, the new one gets `doc_id: "7.5"` (README=7.0, template=7.1, ADR-001=7.2, ADR-002=7.3... wait, count from actual files).

Simpler: run the index generator after writing the file — it will assign the correct position automatically.

### Step 3 — Create the file

Filename format: `ADR-NNN-kebab-case-title.md`

Rules:
- Lowercase only
- Hyphens between words, no underscores
- Title should be a noun phrase describing the decision, not a question
- Good: `ADR-003-async-task-queue-selection.md`
- Bad: `ADR-003-which-queue-should-we-use.md`

```bash
# file lives at:
docs/adr/ADR-NNN-kebab-case-title.md
```

### Step 4 — Fill every section

Fill in this order:

1. **Frontmatter** — `doc_id`, `title`, `section: "ADR"`, `summary` (one sentence: status + what was decided), `updated` (today's date)
2. **Status** — set to `Accepted` if the decision is already implemented or locked; `Proposed` if still pending review
3. **Date** — today's date in `YYYY-MM-DD`
4. **Context** — explain the situation that made this decision necessary; include constraints
5. **Decision** — state the exact choice made, specific enough that a new contributor could implement it
6. **Consequences** — split into Easier / Harder / Risks accepted / Follow-up work
7. **Alternatives Considered** — at least two rows in the table; be honest about why each was rejected
8. **References** — link to code, prior ADRs, and architecture docs affected

**Common trap:** Skipping Alternatives because the decision felt obvious. Even obvious decisions need alternatives documented — they prevent the decision being re-litigated by future agents or contributors who don't have the context.

### Step 5 — Update the index

```bash
make adr-index
```

This regenerates `docs/adr/README.md` from the ADR files. Verify the new entry appears correctly in the table.

### Step 6 — Link from the PR

In the PR description, include:

```
## Architecture Decision
See [ADR-NNN: Decision Title](docs/adr/ADR-NNN-kebab-case-title.md)
```

This is required by `.cursor/rules/global.md`. The PR that implements the decision and the ADR that documents it must be linked.

---

## Superseding a Prior ADR

When a new decision replaces an existing one:

1. In the **new ADR**: add `**Supersedes:** ADR-NNN` on a line directly below Status
2. In the **old ADR**: change its Status line to `Superseded by ADR-NNN` and update `updated` date
3. Run `make adr-index` — the old ADR will appear with Superseded status in the table

Never delete old ADRs. The historical record of why decisions were made (including wrong ones) is valuable.

---

## Validation Checklist

Before committing:

- [ ] Filename matches `ADR-NNN-kebab-case-title.md` (lowercase, hyphens, zero-padded number)
- [ ] Frontmatter complete: `doc_id`, `title`, `section: "ADR"`, `summary`, `updated`
- [ ] Status is set (not left as the pipe-separated options from the template)
- [ ] Date is set in `YYYY-MM-DD` format
- [ ] Context section explains WHY the decision was needed, not just what was decided
- [ ] Decision section is specific and concrete — no hedging language
- [ ] Consequences split into Easier / Harder / Risks accepted
- [ ] Alternatives table has at least two rows with honest rejection reasons
- [ ] References section has at least one link
- [ ] No `TODO` or template placeholder text remaining
- [ ] `make adr-index` run and `docs/adr/README.md` updated
- [ ] PR description links to the ADR

---

## Common Failure Modes

**"Alternatives Considered" is empty or has one row.**
Every decision has alternatives — if you can't name two, you haven't thought hard enough. Common alternatives: "do nothing", "use a different library", "defer the decision". Always include at least "status quo" as an alternative with why it was rejected.

**Decision section is vague.**
"We will use a queue for async work" is not a decision. "We will use Celery with Redis as the broker, task results stored for 24 hours, max 3 retries with exponential backoff" is a decision. Be specific enough that an agent implementing it has no ambiguity.

**Status left as "Proposed" after implementation.**
If the code is already merged, the status should be "Accepted". "Proposed" means the decision is still open to challenge.

**ADR written after the fact with no context.**
ADRs written retrospectively often skip the forces that made the decision necessary. If writing after the fact, interview the original decision-maker (or read the PR thread) to reconstruct the context before writing.

**Index not updated.**
Always run `make adr-index` before committing. The `docs/adr/README.md` is auto-generated — hand-editing it is forbidden.

---

## Handoff Expectations

- ADR file committed to `docs/adr/`
- `docs/adr/README.md` regenerated via `make adr-index`
- If any `docs/architecture/` files are affected by the decision, their content updated and status set to `"current"`
- PR description contains ADR link
- If decision supersedes a prior ADR, that ADR's status updated

---

## Related Skills

`skills/repo-governance/writing-adrs.md` — superseded by this skill

## Related Procedures

`docs/procedures/implement-change.md` — ADR before implementation

## Related Rules

- `.cursor/rules/global.md` — architectural decisions need ADR + PR link
- `.cursor/rules/documentation.md` — when ADRs are required
- `AGENTS.md §8` — documentation update requirements
