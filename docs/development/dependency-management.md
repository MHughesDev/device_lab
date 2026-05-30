---
doc_id: "3.2"
title: "dependency management"
section: "Development"
summary: "How Python dependencies are declared, upgraded, and reviewed in this repo."
updated: "2026-04-17"
---

# 3.2 — dependency management

<!-- CROSS-REFERENCES -->
<!-- - Referenced by: docs/development/README.md, README.md -->

**Purpose:** How Python dependencies are declared, upgraded, and reviewed in this repo.

## 3.2.1 Overview

How Python dependencies are declared, upgraded, and reviewed in this repo. See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

## 3.2.2 Where dependencies live

- **Runtime and dev:** `pyproject.toml` (`[project.dependencies]` and `[project.optional-dependencies] dev`).
- **Locking:** Use committed constraints in `pyproject.toml`; pin major upgrades deliberately.

## 3.2.3 Upgrade workflow

1. Edit version constraints in `pyproject.toml`.
2. Reinstall: `pip install -e ".[dev]"`.
3. Run `make lint`, `make typecheck`, `make test`.
4. Run `make security-scan` / `make security:scan` for dependency-related security review.
5. Document notable upgrades in `CHANGELOG.md` when behavior or operators are affected.

## 3.2.4 Related

- [docs/procedures/dependency-upgrade.md](../procedures/dependency-upgrade.md)
- [skills/security/dependency-review.md](../../skills/security/dependency-review.md)
