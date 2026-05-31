---
alwaysApply: true
description: Documentation update triggers. When docs MUST be updated alongside code changes.
---

# .cursor/rules/documentation.md


## Environment variables

1. Add/remove/change meaning of an env var → update **`.env.example`** and **`docs/development/environment-vars.md`**.
2. Run **`scripts/env-var-sync.py`** (or the Makefile wrapper) when present to catch drift.

## API surface

1. New/changed/removed routes → **`docs/api/endpoints.md`**.
2. New/changed error **`code`** values → **`docs/api/error-codes.md`**.
3. Before releases, consider OpenAPI diff scripts if present in **`scripts/`**.

## Behavior and operations

1. Deployment/config behavior → **`docs/operations/configuration.md`** or the specific ops doc.
2. Docker/Compose edits → **`docs/operations/docker.md`**.
3. Kubernetes edits → **`docs/operations/kubernetes.md`**.
4. Auth/security behavior → relevant **`docs/security/`** file.
5. Queue semantics → **`queue/QUEUE_INSTRUCTIONS.md`** and **`docs/queue/queue-system-overview.md`**.
6. Significant architecture choices → new **`docs/adr/`** entry using **`docs/adr/template.md`**.

## Procedures

1. If a **`make`** target or step order in a procedure changes, update that **`docs/procedures/*.md`** file.

## Generated docs

1. If **`make docs:generate`** exists, prefer editing **sources** and regenerating rather than hand-editing generated sections.
2. CI should fail on drift between generated docs and code when that check is enabled.
