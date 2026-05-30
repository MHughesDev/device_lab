---
doc_id: "17.1"
title: "common issues"
section: "Troubleshooting"
summary: "Common development issues and solutions."
updated: "2026-04-17"
---

# 17.1 — common issues

<!-- Per spec §26.12 item 377 -->

**Purpose:** Common development issues and solutions. Per spec §26.12 item 377.

## 17.1.1 Port Conflicts

Port 8000 already in use → change API_PORT in .env. Port 5432 in use → change DB port in docker-compose.yml or stop conflicting service.

## 17.1.2 Docker Issues

Docker not running → start Docker Desktop or `sudo systemctl start docker`. Permission errors → add user to docker group.

## 17.1.3 Migration Failures

Alembic revision not found → run `make db:reset`. Conflict in migration history → check `alembic history`.

## 17.1.4 CI Drift (docs:check failing)

Generated docs out of sync → run `make docs:generate` and commit the result.

## 17.1.5 Python Version Issues

Wrong Python version → use pyenv/asdf: `pyenv install 3.12` then `pyenv local 3.12`.

## 17.1.6 Pre-commit Hook Failures

detect-secrets false positive → run `detect-secrets scan > .secrets.baseline && git add .secrets.baseline`.
