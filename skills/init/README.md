# skills/init/README.md

**Purpose:** Index for initialization skills. The flow has two canonical skills, run in order; the first is optional (use it only when `IDEA.md` is not yet filled out).

## When to invoke

- **`idea_author.md`** — when `IDEA.md` is the blank template (or partially filled) and the developer has source material or a prompt they want turned into a real intake document.
- **`repo_initialize.md`** — once `IDEA.md` is filled out end-to-end and the developer asks for the repo to be initialized for their product.

## Prerequisites

- Read root `AGENTS.md`, `apps/api/AGENTS.md`, `apps/web/AGENTS.md`.
- Read the current `IDEA.md` to see what is already filled and what is stub.
- Read `queue/QUEUE_INSTRUCTIONS.md` before running `repo_initialize` — every row it creates must conform to that schema.

## Skills in this category

| Step | Skill | Purpose |
|------|-------|---------|
| 1 (optional) | [`idea_author.md`](idea_author.md) | Turn raw input (notes, PRD, prompt, partial draft) into a completely filled-out `IDEA.md`. Replaces the blank stub. Never invents product decisions; gaps become §19 open questions. |
| 2 (required) | [`repo_initialize.md`](repo_initialize.md) | Read the completed `IDEA.md`, refresh design docs, seed initial MVP queue rows, surface remaining open questions as blocked `category=human-ops` rows. Never writes product code. |

## Invocation flow

```
raw materials  ─►  idea_author.md  ─►  filled IDEA.md  ─►  repo_initialize.md  ─►  spec + docs + MVP queue
                  (optional)            (canonical input)    (required)             (executed later via queue rows)
```

1. (Optional) Developer asks an agent to run `idea_author.md` against their source material. Output: a completed `IDEA.md`.
2. Developer reviews and edits `IDEA.md` if needed.
3. Developer asks an agent to run `repo_initialize.md`. Output: refreshed spec/docs + initial MVP queue rows + blocked rows for any remaining open questions.

Either step can be skipped if its inputs are already in the right shape:

- If the developer wrote `IDEA.md` by hand, skip step 1.
- If only `IDEA.md` is requested (no initialization), stop after step 1.

There is no `make idea:*` command. There is no multi-skill phased pipeline. Initialization is two AI-judged procedures, not a shell orchestrator.

## Related resources

- Input contract: [`/IDEA.md`](../../IDEA.md)
- Invocation prompt for step 2: [`prompts/repo_initializer.md`](../../prompts/repo_initializer.md)
- Queue lifecycle: [`queue/QUEUE_INSTRUCTIONS.md`](../../queue/QUEUE_INSTRUCTIONS.md)
- Founding ADR: [`docs/adr/0001-initial-template-architecture.md`](../../docs/adr/0001-initial-template-architecture.md)
