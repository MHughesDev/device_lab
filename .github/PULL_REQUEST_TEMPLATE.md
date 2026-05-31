## Summary
<!-- 1-2 sentences: what changed and why -->

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| <!-- Criterion 1 from queue/task --> | <!-- [x] Met / [ ] Not met / [~] Partial --> | <!-- Evidence of completion --> |
| <!-- Criterion 2 --> | | |

## Commands Run (with key output)

<!-- Paste the output of each command run during validation -->

```bash
$ make preflight
# Output:

```

```bash
$ make lint
# Output:

```

```bash
$ make fmt-check
# Output:

```

```bash
$ make typecheck
# Output:

```

```bash
$ make test  # or make test:affected
# Output:

```

## Files Changed

| File | Change Description |
|------|-------------------|
| <!-- path/to/file --> | <!-- What changed and why --> |
| <!-- path/to/file --> | <!-- What changed and why --> |

## Residual Risks

<!-- List any known risks, edge cases, or potential issues that remain -->
- Risk 1: <!-- description and mitigation -->
- Risk 2: <!-- description and mitigation -->

## Follow-ups

<!-- List any out-of-scope items that became new queue items or issues -->
- [ ] <!-- Follow-up 1 -->
- [ ] <!-- Follow-up 2 -->

---

## Operator Checklist (for queue PRs — human operator)

- [ ] PR reviewed and approved
- [ ] CI is green
- [ ] PR merged to `main`
- [ ] `make queue:archive-top` or `make queue:archive QUEUE_ID=<id>` run
- [ ] `make queue:validate` passes
- [ ] `make queue:pr-merge` run (if using GitHub CLI)
- [ ] Feature branch deleted locally and on remote
