#!/usr/bin/env bash
# scripts/image-scan.sh
# Scan Docker image with Trivy (requires trivy in PATH).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${IMAGE_TAG:-template-api:local}"
if ! command -v trivy >/dev/null 2>&1; then
  echo "trivy not installed; skipping image scan." >&2
  exit 0
fi
exec trivy image --config "$ROOT/trivy.yaml" --exit-code 0 --severity HIGH,CRITICAL "$TAG"
