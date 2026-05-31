#!/usr/bin/env bash
# scripts/image-build.sh
# Build API Docker image.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${IMAGE_TAG:-template-api:local}"
docker build -t "$TAG" -f "$ROOT/apps/api/Dockerfile" "$ROOT"
