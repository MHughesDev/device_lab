# packages/contracts/AGENTS.md

<!-- Per spec §26.9 item 238 -->

**Purpose:** Scoped agent instructions for the contracts package. Emphasizes backward compatibility, versioning, and testing contract changes. Per spec §26.9 item 238.

## Scope

This package contains shared Pydantic models that constitute the API contract between bounded contexts and between the API and external clients. Root AGENTS.md remains supreme for all repo-wide policy.

## Backward Compatibility Rules

The most critical constraint for this package:
1. NEVER remove a field from any model in packages/contracts/
2. NEVER rename a field in any model
3. NEVER change a field's type to an incompatible type
4. New fields may be added only as OPTIONAL (with default=None)
5. Any change that could break existing clients requires an ADR
6. Use packages/contracts/v2/ (namespace) for breaking changes if ever needed

## Versioning

Current version: v1 (all models are in the default namespace). When breaking changes are unavoidable: create packages/contracts/v2/ namespace and migrate clients deliberately with a deprecation period.

## Testing Contract Changes

Any change to models in this package requires:
- Existing tests must still pass (backward compatibility)
- New test confirming the added field works
- Run openapi-diff.py to detect breaking changes in the generated API schema
