---
doc_id: "11.1"
title: "coverage policy"
section: "Quality"
summary: "Coverage floor definition and ratcheting mechanism."
updated: "2026-04-17"
---

# 11.1 — coverage policy

<!-- Per spec §26.5 items 183-186 -->

**Purpose:** Coverage floor definition and ratcheting mechanism.

## 11.1.1 Overview

Coverage floor definition and ratcheting mechanism. See [AGENTS.md](../../AGENTS.md) for validation commands and [spec/spec.md](../../spec/spec.md) for the full specification.

<!-- coverage-floor: 55 -->
The default floor matches `fail_under` in `pyproject.toml` (pytest coverage). The `coverage-ratchet` skill may update this comment when coverage improves.
