---
doc_id: "5.25"
title: "validate change"
section: "Procedures"
summary: "SOP: Run full validation matrix before opening PR."
updated: "2026-04-17"
---

# 5.25 — validate change

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: AGENTS.md §7, prompts/reviewer_critic.md -->
<!-- - Uses: make audit:self -->

**Purpose:** SOP: Run full validation matrix before opening PR. Per spec §26.5 item 142 and §8.3.

## 5.25.1 Purpose

Full validation before PR prevents CI failures and reviewer-discovered issues that waste cycles. This is the last checkpoint before the change is shared.

## 5.25.2 Trigger / When to Use

After implement-change.md is complete. Before running open-pull-request.md.

## 5.25.3 Prerequisites

All implementation commits on branch. Tests written and expected to pass.

## 5.25.4 Exact Commands

`make fmt`, `make lint`, `make typecheck`, `make test`, `make queue:validate`, `make docs:check`, `make security:scan`, `make audit:self`

Canonical names: `make lint`, `make typecheck`, `make test`, `make security:scan` (run from the repository root).

## 5.25.5 Ordered Steps

1. `make fmt` — apply formatting (auto-fix mode); commit if changes made
2. `make lint` — must produce zero errors
3. `make typecheck` — must produce zero errors
4. `make test` — all tests pass, coverage above floor
5. (If queue files touched) `make queue:validate` — queue schema valid
6. (If docs updated) `make docs:check` — no broken links, generated docs match source
7. (If security-adjacent) `make security:scan` — no unaccepted HIGH/CRITICAL findings
8. `make audit:self` — spec compliance check
9. Capture all output — paste key lines in PR description

## 5.25.6 Expected Artifacts / Outputs

Validation report with all commands run and their pass/fail status. To be included in PR description.

## 5.25.7 Validation Checks

- [ ] make fmt: no formatting changes
- [ ] make lint: zero errors
- [ ] make typecheck: zero errors
- [ ] make test: all pass, coverage above floor
- [ ] make audit:self: no BLOCKING findings

## 5.25.8 Rollback or Failure Handling

If any check fails: fix before opening PR. Do not open PRs with known failures — document why if exception is needed.

## 5.25.9 Handoff Expectations

All checks passing. Validation report ready for PR description.
