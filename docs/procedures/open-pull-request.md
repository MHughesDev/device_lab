---
doc_id: "5.17"
title: "open pull request"
section: "Procedures"
summary: "SOP: Create PR with title, description template, evidence, labels, queue linkage."
updated: "2026-04-17"
---

# 5.17 — open pull request

<!-- CROSS-REFERENCES -->
<!-- - Template: .github/PULL_REQUEST_TEMPLATE.md -->
<!-- - Referenced by: AGENTS.md §4 (Branch and PR Policy) -->

**Purpose:** SOP: Create PR with title, description template, evidence, labels, queue linkage. Per spec §26.5 item 143 and §8.3.

## 5.17.1 Purpose

A well-formed PR provides all context needed for review without the reviewer asking questions. Evidence is embedded in the description.

## 5.17.2 Trigger / When to Use

After validate-change.md passes. All CI checks expected to be green.

## 5.17.3 Prerequisites

All validation passing. Branch pushed to origin. PR template (.github/PULL_REQUEST_TEMPLATE.md) read.

## 5.17.4 Exact Commands

`git push -u origin <branch>`, then open PR via GitHub UI or `gh pr create`.

## 5.17.5 Ordered Steps

1. Push branch: `git push -u origin queue/<id>-slug`
2. Open PR targeting `main` branch
3. Title format: `[<queue-id>] <type>(<scope>): <description>` (max 72 chars)
4. Fill description using .github/PULL_REQUEST_TEMPLATE.md:
   - Summary of changes (one paragraph)
   - Queue item ID with link to row
   - Files changed list
   - Commands run with key output (paste validation results)
   - Tests added/updated
   - Documentation updated
   - Risks and follow-ups
   - Completion checklist
5. Add labels: category (api, docs, infra), type (feature, fix, chore, security)
6. Wait for CI to complete — if CI fails, fix before requesting review

## 5.17.6 Expected Artifacts / Outputs

Open PR with green CI, queue ID in title, full evidence in description.

## 5.17.7 Validation Checks

- [ ] PR title contains queue ID
- [ ] CI passing (all checks green)
- [ ] Description has evidence (commands run, output)
- [ ] Labels added

## 5.17.8 Rollback or Failure Handling

If CI fails after PR opened: fix on the same branch (add more commits), do not reopen.

## 5.17.9 Handoff Expectations

PR URL in queue notes. Human reviewer can approve and merge.
