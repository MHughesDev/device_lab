# skills/ai-rag/embedding-refresh.md

<!-- CROSS-REFERENCES -->
<!-- - Profile: optional AI/RAG profile -->
<!-- - Related docs: docs/architecture/ai-rag-chromadb.md -->

**Purpose:** [OPTIONAL] Frontend/mobile skill. Enable the web or mobile profile before relying on this.

## Purpose
What this AI/RAG skill enables.

## When to Invoke
Specific triggers (only when AI profile is enabled).

## Prerequisites
AI profile enabled, ChromaDB running, packages/ai/ configured.

## Relevant Files/Areas
packages/ai/, docs/architecture/ai-rag-chromadb.md

## Step-by-Step Method
Numbered AI/RAG procedure steps.

## Command Examples
docker compose --profile ai up, relevant Python CLI commands.

## Validation Checklist
- [ ] AI profile enabled and configured
- [ ] ChromaDB accessible
- [ ] Kill switch tested

## Common Failure Modes
ChromaDB connectivity, embedding failures.

## Handoff Expectations
AI feature verified, kill switch tested.

## Related Procedures
docs/procedures/enable-profile.md

## Related Prompts
prompts/implementation_agent.md

## Related Rules
.cursor/rules/security.md (AI_ENABLED kill switch)
