# prompts/README.md

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: AGENTS.md §14, docs/prompts/README.md, docs/prompts/index.md -->
<!-- - Procedure: docs/procedures/add-prompt-template.md -->

**Purpose:** Prompt library overview. Documents the metadata convention (YAML front matter), how to add new templates, naming rules, and links to docs/prompts/. Per spec §26.3 item 19.

## Overview

Brief description of the prompt library. This directory contains reusable, versioned prompt templates for recurring agent roles. Each template has YAML front matter with metadata and a prompt body with role definition, step-by-step instructions, and validation checklist.

**Template contract:** Prompt bodies should align with root **[AGENTS.md](../AGENTS.md)** — including **§14** (preamble: README + AGENTS + skill search). This repository does **not** require a project-specific MCP connection for agents; optional MCP servers are editor/vendor integrations, not part of the baseline workflow.

## Metadata Convention

Describe the chosen metadata format — YAML front matter (inline, not paired .meta.yaml). Show the exact required fields with one-line descriptions:
```yaml
---
purpose: "What this template does in one sentence"
when_to_use: "Specific trigger for invoking this template"
required_inputs:
  - name: "Input name"
    description: "What this input is"
expected_outputs:
  - "Output artifact 1"
  - "Output artifact 2"
validation_expectations:
  - "What must be true for the output to be correct"
constraints:
  - "What this template does NOT do"
linked_commands:
  - "make target:name"
linked_procedures:
  - "docs/procedures/relevant-procedure.md"
linked_skills:
  - "skills/category/relevant-skill.md"
---
```

## Naming Rules

Rules for template file naming:
- Use snake_case for template names (e.g., `task_planner.md`, not `task-planner.md` or `TaskPlanner.md`)
- Name reflects the agent role, not the action (e.g., `implementation_agent.md` not `implement.md`)
- Subroutine templates prefix with their caller context (e.g., `skill_searcher.md`)

## Template Index

Table of all templates in this directory. Columns: Template file, Role, When to use. One row per template file. Maintained manually (or via `make docs:generate`):
- repo_initializer.md — Master initialization prompt
- domain_modeler.md — Domain analysis and context mapping
- profile_configurator.md — Profile enablement and configuration
- task_planner.md — Task decomposition and planning
- implementation_agent.md — Code change execution
- reviewer_critic.md — Adversarial code review
- test_writer.md — Test authoring
- debugger.md — Failure isolation
- refactorer.md — Behavior-preserving refactoring
- migration_author.md — Database migrations
- queue_processor.md — Queue item execution (implementation; pair with queue_worker_executor.md)
- queue_worker_executor.md — **Canonical queue worker**: read QUEUE_INSTRUCTIONS + QUEUE_AGENT_PROMPT; **never** edit queue.csv / queuearchive.csv
- release_manager.md — Release preparation
- dependency_upgrade_agent.md — Dependency upgrades
- security_review_agent.md — Security-focused review
- incident_triage_agent.md — Incident classification
- performance_audit_agent.md — Performance review
- repo_bootstrap_agent.md — Fresh clone to green dev
- skill_authoring_agent.md — Skill creation/update
- rule_authoring_agent.md — Rule creation/update
- skill_searcher.md — Task-to-skill matching subroutine

## How to Add a New Template

Brief steps for adding a new template. Link to docs/procedures/add-prompt-template.md for the full SOP. Summary:
1. Create prompts/<name>.md with YAML front matter (all §7.2 fields)
2. Write prompt body with preamble (mandatory skill search reference), role definition, steps, validation checklist
3. Update docs/prompts/index.md with the new template
4. Update this README table
5. PR with evidence: linked skills/procedures tested, validation checklist verified
