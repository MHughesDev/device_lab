#!/usr/bin/env bash
# scripts/preflight.sh
# Fast pre-flight checks before lint/test cycle. Runs in <10s on clean tree.
# Checks: format, lint (subset), import order, file headers, prompt skill-search.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ERRORS=0

echo "=== Preflight checks (fast fail-fast validation) ==="

# 1. Format check (fast)
echo "→ Checking formatting..."
if ! python3 -m ruff format --check apps/api/app packages 2>/dev/null; then
    echo "  ✗ Format check failed. Run 'make fmt' to fix."
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ Format OK"
fi

# 2. Lint subset (fast checks only - no complex analysis)
echo "→ Running fast lint checks..."
if ! python3 -m ruff check --select=E,W,I,N --quiet apps/api/app packages 2>/dev/null; then
    echo "  ✗ Fast lint failed. Run 'make lint' for details."
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ Fast lint OK"
fi

# 3. Import order check
echo "→ Checking import order..."
if ! python3 -m ruff check --select=I --quiet apps/api/app packages 2>/dev/null; then
    echo "  ✗ Import order check failed."
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ Import order OK"
fi

# 4. Python file headers (quick grep)
echo "→ Checking Python file headers..."
MISSING_HEADER=0
for f in $(find apps/api/app packages -name "*.py" -not -path "*/alembic/*" -not -name "__init__.py" | head -20); do
    if ! head -1 "$f" | grep -q "^#"; then
        MISSING_HEADER=$((MISSING_HEADER + 1))
    fi
done
if [ $MISSING_HEADER -gt 0 ]; then
    echo "  ⚠ $MISSING_HEADER files missing header comments (info only)"
fi

# 5. Check prompts for skill-search reference (policy check)
echo "→ Checking prompt templates for skill-search reference..."
MISSING_PREAMBLE=0
for f in prompts/*.md; do
    if [ -f "$f" ]; then
        if ! grep -q "skill search\|skill_searcher\|skills:list" "$f" 2>/dev/null; then
            MISSING_PREAMBLE=$((MISSING_PREAMBLE + 1))
            echo "  ⚠ $f missing skill-search reference"
        fi
    fi
done
if [ $MISSING_PREAMBLE -eq 0 ]; then
    echo "  ✓ Prompt skill-search references OK"
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✓ Preflight passed — proceeding to full validation"
    exit 0
else
    echo "✗ Preflight failed with $ERRORS error(s) — fix before full validation"
    exit 1
fi
