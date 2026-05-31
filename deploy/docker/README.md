# deploy/docker/README.md

<!-- Per spec §26.10 item 246 -->

**Purpose:** Docker deployment documentation. References docker-compose.yml, profiles, and image build. Per spec §26.10 item 246.

## Overview

Docker is used for both local development and production deployment. The API container image is built from apps/api/Dockerfile using a multi-stage build.

## Profiles Available

Docker Compose profiles:
- (default) — API service only (SQLite for local dev)
- db — Add PostgreSQL
- ai — Add ChromaDB vector store
- worker — Add Redis + background worker
- Enable multiple: docker compose --profile db --profile ai up

## Build Instructions

Build the API image: `make image:build`. The image tag format: `<registry>/<org>/<repo>:sha-<commit>`. In CI: image is built and scanned (make image:scan) on every PR.

## Production Considerations

Key differences from dev:
- API_DEBUG=false (enforced by config validator)
- PostgreSQL instead of SQLite (DATABASE_URL points to managed PostgreSQL)
- No volume mounts for source code (immutable image)
- Resource limits set in docker-compose.yml (or K8s manifests)
