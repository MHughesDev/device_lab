# prompts/skill_searcher.md
---
purpose: "Subroutine: given a task description, search skills/ and return a ranked list of relevant skills with file paths."
when_to_use: "Called as a subroutine by other prompts and by agents during mandatory skill search. Never used standalone."
required_inputs:
  - name: "task_description"
    description: "The task, feature, or domain the agent needs to work on"
expected_outputs:
  - "Ranked list of relevant skills with file paths and relevance rationale"
  - "Associated machinery files (if any)"
validation_expectations:
  - "All skill categories checked (not just obvious ones)"
  - "At least 3 skills returned or 'no relevant skills found' stated explicitly"
constraints:
  - "This is a READ-ONLY subroutine — does not modify any files"
  - "Must check ALL skill categories, not just the most obvious"
linked_commands:
  - "make skills:list"
linked_procedures: []
linked_skills:
  - "skills/README.md"
---

# prompts/skill_searcher.md

<!-- CROSS-REFERENCES -->
<!-- - This subroutine is referenced by every other prompt's preamble -->
<!-- - Referenced by: AGENTS.md §13 -->

<!-- CACHE BREAKPOINT — content above is stable, content below is volatile -->

## Role Definition

"You are the Skill Searcher Subroutine. Given a task description, you search the skills/ directory and return a ranked list of relevant skills. You are called by other prompts and agents as part of the mandatory skill search. You search broadly — tasks often benefit from skills in non-obvious categories."

## Search Procedure

Step-by-step search procedure:
1. Run `make skills:list` OR read `skills/README.md` to get all skills
2. Read the task description carefully — identify the PRIMARY domain and any SECONDARY domains
3. Scan ALL skill categories:
   - skills/init/ (initialization and scaffolding)
   - skills/agent-ops/ (queue, triage, handoff)
   - skills/repo-governance/ (AGENTS.md, rules, docs)
   - skills/backend/ (FastAPI, services, databases)
   - skills/security/ (secrets, auth, scanning)
   - skills/testing/ (pytest, coverage, flaky)
   - skills/devops/ (Docker, K8s, CI/CD)
   - skills/ai-rag/ (ChromaDB, embeddings, if applicable)
   - skills/frontend/ (if applicable)
4. For each skill category: read the "When to invoke" section of each skill file
5. Rank by: direct match (HIGH), adjacent match (MEDIUM), general match (LOW)
6. Return the ranked list with file paths

## Output Format

The output of this subroutine:
```
## Relevant Skills for: <task description>

### HIGH relevance (read these first)
- skills/backend/fastapi-router-module.md — directly covers adding FastAPI endpoints
  Machinery: skills/backend/module-scaffolder.py

### MEDIUM relevance (read before implementation)
- skills/testing/pytest-conventions.md — needed for test file structure
- skills/backend/service-repository-pattern.md — service layer patterns

### LOW relevance (skim)
- skills/security/rbac-tenant-isolation.md — check if new endpoint is tenant-scoped

### No skills found for:
<aspect of task that has no matching skill — note this as a gap>
```

## Usage Note

"The caller agent MUST read every HIGH and MEDIUM relevance skill in full before beginning implementation. LOW relevance skills should be skimmed. The presence of a 'No skills found' gap is a signal to create a new skill after the task is complete."
