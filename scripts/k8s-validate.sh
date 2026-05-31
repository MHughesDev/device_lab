#!/usr/bin/env bash
# scripts/k8s-validate.sh
# Validate rendered manifests (kubeconform optional).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OVERLAY="${OVERLAY:-dev}"
DIR="$ROOT/deploy/k8s/overlays/$OVERLAY"

render() {
  if command -v kubectl >/dev/null 2>&1; then
    kubectl kustomize "$DIR"
    return
  fi
  if command -v kustomize >/dev/null 2>&1; then
    kustomize build "$DIR"
    return
  fi
  echo "Skipping: kubectl/kustomize not installed" >&2
  exit 0
}

if command -v kubeconform >/dev/null 2>&1; then
  render | kubeconform -strict -summary
else
  render >/dev/null
  echo "k8s:validate OK (kubeconform not installed — syntax only)"
fi
