#!/usr/bin/env bash
# scripts/k8s-render.sh
# Render Kustomize overlay to stdout (kubectl or kustomize CLI).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OVERLAY="${OVERLAY:-dev}"
DIR="$ROOT/deploy/k8s/overlays/$OVERLAY"

if command -v kubectl >/dev/null 2>&1; then
  exec kubectl kustomize "$DIR"
fi
if command -v kustomize >/dev/null 2>&1; then
  exec kustomize build "$DIR"
fi
echo "Install kubectl or kustomize to render manifests." >&2
exit 1
