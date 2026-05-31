# prompts/profile_configurator.md
---
purpose: "Enable or disable optional profiles based on IDEA.md §5 selections. Configures Compose, env vars, package stubs, and documentation."
when_to_use: "During initialization Phase 4, or when enabling a profile post-initialization."
required_inputs:
  - name: "profiles_to_enable"
    description: "List of profiles to enable from IDEA.md §5: web, mobile, workers, ai-rag, multi-tenancy, etc."
  - name: "idea_md"
    description: "Full IDEA.md for context (archetype, constraints)"
expected_outputs:
  - "Configured docker-compose.yml with profile services enabled"
  - "Updated .env.example with profile-specific env vars"
  - "Package stubs created (packages/ai/, packages/tasks/ implementations)"
  - "Docs updated in docs/optional-clients/ for each profile"
validation_expectations:
  - "docker compose config --profiles <profile> succeeds for each enabled profile"
  - "make test passes with profiles configured"
constraints:
  - "Does not enable profiles not selected in IDEA.md §5 (or later override)"
  - "Profile enablement is additive — does not disable other profiles"
linked_commands:
  - "make profile:enable"
linked_procedures:
  - "docs/procedures/enable-profile.md"
  - "docs/procedures/add-optional-app-profile.md"
linked_skills:
  - "skills/init/profile-resolver.md"
  - "skills/devops/compose-profiles.md"
---

# prompts/profile_configurator.md


## Preamble

Standard mandatory skill search preamble. Must read skills/devops/compose-profiles.md and skills/init/profile-resolver.md before configuring any profile.

## Role Definition

"You are the Profile Configurator. You enable optional system profiles based on IDEA.md §5 selections. Each profile has specific files to create, env vars to add, Compose services to enable, and documentation to update."

<!-- CACHE BREAKPOINT — content above is stable, content below is volatile -->

## Per-Profile Configuration Matrix

For each profile, exact steps:

**Web frontend:**
- Create apps/web/ directory with README.md and AGENTS.md
- Add web service stub to docker-compose.yml (if applicable)
- Update docs/optional-clients/web.md with project-specific setup

**Mobile app:**
- Create apps/mobile/ directory with README.md and AGENTS.md
- Update docs/optional-clients/mobile.md

**Background workers:**
- Add worker and redis services to docker-compose.yml
- Add BROKER_URL, RESULT_BACKEND_URL to .env.example
- Ensure packages/tasks/ has concrete implementation

**AI/RAG (ChromaDB):**
- Add chroma service to docker-compose.yml (profile: ai)
- Add CHROMA_HOST, CHROMA_PORT, AI_ENABLED, EMBEDDING_PROVIDER to .env.example
- Ensure packages/ai/ has ChromaDB implementation enabled

**Multi-tenancy:**
- Verify TenantContextMiddleware is active in main.py
- Set MULTI_TENANCY_ENABLED=true in .env.example
- Add tenant fixtures to apps/api/tests/conftest.py

## Validation Checklist

- [ ] Each enabled profile: Compose service present and valid
- [ ] Each enabled profile: env vars added to .env.example with comments
- [ ] Each enabled profile: documentation updated
- [ ] docker compose config --profiles <each_profile> succeeds
- [ ] make test passes
- [ ] skills/devops/compose-profiles.md consulted for each profile
