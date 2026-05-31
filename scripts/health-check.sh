#!/usr/bin/env bash
# scripts/health-check.sh
# GET /api/v1/utils/health-check/ on local API (default http://127.0.0.1:8000).

set -euo pipefail

BASE="${HEALTHCHECK_URL:-http://127.0.0.1:8000}"
curl -fsS "$BASE/api/v1/utils/health-check/" | head -c 200
echo
