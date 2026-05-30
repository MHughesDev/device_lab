---
doc_id: "5.12"
title: "handoff"
section: "Procedures"
summary: "SOP: Complete handoff — files changed, commands run, results, risks, follow-ups."
updated: "2026-04-17"
---

# 5.12 — handoff

<!-- CROSS-REFERENCES -->
<!-- - Skill: skills/agent-ops/implementation-handoff.md -->
<!-- - Machinery: skills/agent-ops/handoff-template-generator.py -->

**Purpose:** SOP: Complete handoff — files changed, commands run, results, risks, follow-ups. Per spec §26.5 item 144 and §8.3.

## 5.12.1 Purpose

The handoff is the agent's audit trail. A complete handoff enables the next agent or human reviewer to understand what happened without any additional context from the originating agent.

## 5.12.2 Trigger / When to Use

After all implementation is complete, before or alongside opening the PR. Also when stopping due to a blocker.

## 5.12.3 Prerequisites

Implementation done (or explicitly blocked). Validation run.

## 5.12.4 Exact Commands

`python skills/agent-ops/handoff-template-generator.py --queue-id <id>` — generate pre-filled template

## 5.12.5 Ordered Steps

1. Run handoff-template-generator.py to generate the base template
2. **Files changed**: verify list is complete (git diff --stat HEAD~N)
3. **Commands run**: list each validation command with pass/fail status and key output
4. **Acceptance criteria**: for each criterion — met/not-met/partial with evidence
5. **Risks**: document any residual risks discovered during implementation
6. **Follow-ups**: list any out-of-scope findings (with queue items or issue links)
7. **PR link**: paste PR URL
8. **Queue state**: update queue notes column with PR URL
9. Paste handoff into PR description (it IS the PR description)

## 5.12.6 Expected Artifacts / Outputs

Complete handoff document in PR description. Queue notes updated with PR URL.

## 5.12.7 Validation Checks

- [ ] All files changed listed
- [ ] All commands run listed with output
- [ ] Acceptance criteria addressed
- [ ] Residual risks documented
- [ ] Follow-ups have queue items/issues
- [ ] PR URL in queue notes

## 5.12.8 Rollback or Failure Handling

If partial handoff (blocked): document what was done, what's remaining, what the blocker is. The partial handoff is still required.

## 5.12.9 Handoff Expectations

This procedure IS the handoff. Its output is the handoff document.
