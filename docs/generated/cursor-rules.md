<!-- Generated from: .cursor\rules — do not edit manually -->

## Cursor rules

| Rule | Scope | Summary |
|------|-------|--------|
| `apps-api.md` | globs | Path-scoped rules for apps/api/. Enforces FastAPI patterns, service/repository boundaries, import conventions, and test co-location. |
| `documentation.md` | always | Documentation update triggers. When docs MUST be updated alongside code changes. |
| `global.md` | always | Universal constraints applied to every agent interaction in this repository. |
| `initialization.md` | globs | Guardrails for the AI-driven, documentation-first repo initialization flow. |
| `prompts.md` | globs | Rules for prompt files. Ensures prompts have required YAML front matter and follow the metadata convention. |
| `queue.md` | globs | Queue file invariants. Lifecycle rules, schema enforcement, no row deletion without archive. |
| `security.md` | always | Security invariants. No secrets in code, token handling rules, tenant isolation checks, dependency review triggers. |
| `skills.md` | globs | Rules for skill files. Ensures skills follow the §6.2 structure, include machinery code where applicable, and cross-reference procedures/prompts/rules. |
| `testing.md` | globs | Testing standards. Coverage expectations, naming conventions, fixture patterns, mock boundaries. |
