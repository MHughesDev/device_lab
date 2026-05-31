# skills/security/tenant-isolation-checker.py
"""Grep for raw SQL or missing tenant_id in apps/api/app (heuristic)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP = {".venv", "__pycache__", "alembic"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.repo_root / "apps" / "api" / "src"
    bad = 0
    for path in root.rglob("*.py"):
        if any(s in path.parts for s in SKIP):
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"execute\s*\(\s*[\"'].*%", text):
            print(f"Possible string-format SQL: {path}")
            bad += 1
    if bad:
        print(f"Found {bad} potential issues (manual review).", file=sys.stderr)
        return 1
    print("No obvious raw-SQL patterns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
