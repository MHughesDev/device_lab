---
doc_id: "5.26"
title: "implementation loop"
section: "Procedures"
summary: "Single end-to-end loop from claiming queue work to PR handoff and operator archive."
updated: "2026-05-16"
---

# 5.3 — implementation loop

1. Read `queue/QUEUE_INSTRUCTIONS.md`, `queue/QUEUE_AGENT_PROMPT.md`, and `prompts/queue_worker_executor.md`.
2. Run `make queue:top-item`; treat output contract as source of truth.
3. Plan using `docs/procedures/plan-change.md`.
4. Implement using `docs/procedures/implement-change.md`.
5. Validate using `docs/procedures/validate-change.md`.
6. Open PR using `docs/procedures/open-pull-request.md`.
7. Handoff using `docs/procedures/handoff.md`.
8. Operator (not executor) archives queue item.
