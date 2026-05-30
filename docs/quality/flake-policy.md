---
doc_id: "11.2"
title: "flake policy"
section: "Quality"
summary: "Flaky test policy — detection, quarantine, fix SLA, and root cause tracking."
updated: "2026-04-17"
---

# 11.2 — flake policy

<!-- Per spec §26.5 items 183-186 -->

**Purpose:** Flaky test policy — detection, quarantine, fix SLA, and root cause tracking.

## 11.2.1 Definition

A **flaky test** passes on some runs and fails on others without any code change. Flaky tests:
- Erode trust in CI — teams begin ignoring red builds.
- Mask real failures — a flaky suite hides a genuine regression.
- Slow iteration — engineers re-run CI instead of investigating.

Zero tolerance: every flaky test is a P1 defect against the test itself.

## 11.2.2 Detection

### Automated detection

Run `skills/testing/flaky-detector.py` to execute the suite N times and report any test with mixed outcomes:

```bash
python3 skills/testing/flaky-detector.py --runs 5 --path apps/api/tests
```

Exit code 1 = flaky tests found. Exit code 0 = all stable.

This uses `--junit-xml` to track outcomes per test node ID across runs, not just suite-level pass/fail.

### CI signal

A test is **suspected flaky** if:
- CI fails on a PR but the same commit passes on re-run.
- A test fails in the matrix (`sqlite` or `postgres`) but not the other.

When CI re-running fixes the failure: open a tracking issue immediately before merging.

### Periodic runs

Run the detector weekly (or gate on it in CI). Add to the queue as a recurring maintenance item.

## 11.2.3 Quarantine

When a flaky test is identified:

1. **Mark it immediately:**
   ```python
   @pytest.mark.skip(reason="Flaky — see issue #<N>. Fix SLA: <date>")
   ```
2. **Open a tracking issue** with:
   - Test node ID
   - Failure rate (e.g. "2/5 runs")
   - Last known error output
   - Suspected root cause category (see below)
3. **Add a queue item** in `queue/queue.csv` with the issue link and fix-by date.

Do not quarantine more than 3 tests at once. If more than 3 tests are simultaneously flaky, stop feature work and fix them.

## 11.2.4 Fix SLA

| Priority | Failure rate | SLA |
|----------|-------------|-----|
| P1 | > 50% | Fix within 1 working day |
| P2 | 20–50% | Fix within 3 working days |
| P3 | < 20% | Fix within 1 sprint |

The quarantine `@pytest.mark.skip` **must be removed** when the fix is merged. Never leave a skipped test indefinitely.

## 11.2.5 Root cause categories

Track the root cause in the issue to improve test design:

| Category | Cause | Fix pattern |
|----------|-------|-------------|
| **Time-dependent** | `datetime.now()` called inside test; result depends on clock | Inject fixed datetime via `freezegun` or fixture |
| **Order-dependent** | Test relies on another test's side effects | Use `conftest` fixtures with explicit setup/teardown; `--randomly-seed` to detect |
| **Async race** | `await` without proper synchronisation; event loop state leaking | Use `pytest-asyncio` `event_loop` fixture; don't share state across async tests |
| **External I/O** | Test calls a real HTTP endpoint, file, or DB that is slow/unavailable | Mock at the boundary; use `respx` or `unittest.mock` |
| **Port conflict** | Test binds a port already in use | Use ephemeral ports (port 0) or fixture isolation |
| **Fixture leak** | Session-scoped fixture modified inside a function-scoped test | Mark fixtures with correct scope; use `autouse=True` teardown |
| **Coverage randomness** | `random` without seed | `random.seed(42)` in fixture or use deterministic data |

## 11.2.6 Metrics to track

After each quarter, review:
- Number of flaky tests detected
- Time-to-quarantine (should be < 1 day)
- Time-to-fix (vs SLA)
- Root cause distribution (identify systemic patterns)

Record findings in the post-quarter retrospective (see `docs/repo-governance/improvement-loops.md`).
