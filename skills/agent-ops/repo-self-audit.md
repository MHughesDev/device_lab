# skills/agent-ops/repo-self-audit.md

<!-- CROSS-REFERENCES -->
<!-- - Machinery: skills/agent-ops/repo-self-audit.py -->
<!-- - Related command: .cursor/commands/audit.md -->
<!-- - Make target: make audit:self -->

**Purpose:** [FULL SKILL] How to run and interpret the comprehensive repo self-audit. Verifies spec compliance: required files exist, skills have all sections, prompts have front matter, procedures have required fields, queue schema valid, Make targets documented, file title comments present. Per spec §26.4 item 47.

## Purpose

One paragraph. The repo self-audit is the periodic health check that verifies the repository machine is spec-compliant. It catches drift between the spec and the implementation before it becomes a problem. Running `make audit:self` is mandatory before any major PR and should be run on a weekly/monthly cadence.

## When to Invoke

- Before opening any substantial PR
- After a major implementation phase
- On weekly/monthly audit cadence (document in queue)
- When investigating "the repo feels off" — drift symptoms

## Prerequisites

- Python 3.12+ with virtual environment activated
- `queue/queue.csv` and `queue/queuearchive.csv` exist
- AGENTS.md accessible (for inventory reference)

## Relevant Files/Areas

- `scripts/audit-self.sh` — the shell script that orchestrates the audit
- `skills/agent-ops/repo-self-audit.py` — the Python audit engine
- AGENTS.md §26 — the required file inventory
- `.cursor/rules/global.md` — file title comment standard (§1.7)

## Step-by-Step Method

Numbered steps:
1. Run `make audit:self` (which calls `scripts/audit-self.sh`)
2. Review the output sections:
   - **INVENTORY**: missing required files
   - **TITLE COMMENTS**: files missing §1.7 title comment
   - **SKILL FORMAT**: skills missing §6.2 required sections
   - **PROMPT METADATA**: prompts missing §7.2 front matter fields
   - **PROCEDURE STRUCTURE**: procedures missing §8.3 required sections
   - **QUEUE SCHEMA**: queue.csv/archive.csv header problems
   - **MAKE TARGETS**: §10.2 required targets missing from Makefile
3. Categorize findings: BLOCKING (required file missing) vs WARNING (format issue)
4. For BLOCKING: create queue items or fix immediately
5. For WARNING: create queue items for later remediation
6. Paste the "AUDIT SUMMARY" section in PR description as evidence

## Command Examples

- `make audit:self` — run full audit (primary entry point)
- `python skills/agent-ops/repo-self-audit.py --check inventory` — inventory only
- `python skills/agent-ops/repo-self-audit.py --check queue` — queue schema only
- `python skills/agent-ops/repo-self-audit.py --format json > audit.json` — machine-readable output

## Validation Checklist

- [ ] All BLOCKING findings resolved before PR merge
- [ ] All WARNING findings acknowledged (queued or documented)
- [ ] Audit summary included in PR description
- [ ] No new BLOCKING findings introduced by the current change

## Common Failure Modes

- **Audit not run before PR**: findings discovered by human reviewer instead. Fix: `make audit:self` before any `git push`.
- **Blocking findings ignored**: merging with known spec violations. Fix: treat BLOCKING as a CI blocker.
- **Audit output not saved**: reviewer can't see what was checked. Fix: paste AUDIT SUMMARY in PR description.

## Handoff Expectations

Include the full audit summary in the PR description. State: "Audit run: make audit:self — PASS/FAIL. [N] blocking, [N] warning findings."

## Related Procedures

docs/procedures/validate-change.md, docs/repo-governance/audits.md

## Related Rules

.cursor/rules/global.md (file title comments, §1.7), AGENTS.md §7 (Validation before handoff)

## Machinery

`skills/agent-ops/repo-self-audit.py` — automated audit engine that checks: file inventory (§26), skill format (§6.2), prompt metadata (§7.2), procedure structure (§8.3), queue schema, Make targets (§10.2), file title comments (§1.7). Produces structured Markdown report with BLOCKING/WARNING categorized findings. Invoke: `python skills/agent-ops/repo-self-audit.py` or `make audit:self`.
