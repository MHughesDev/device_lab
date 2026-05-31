# skills/repo-governance/docs-freshness-checker.py
"""Warn if markdown files under docs/ were not modified in last N days."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    stale = 0
    for path in (args.repo_root / "docs").rglob("*.md"):
        r = subprocess.run(
            ["git", "-C", str(args.repo_root), "log", "-1", "--format=%ct", "--", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0 or not r.stdout.strip():
            continue
        ts = int(r.stdout.strip())
        age_days = (datetime.now(UTC).timestamp() - ts) / 86400
        if age_days > args.days:
            print(f"Stale (> {args.days}d): {path.relative_to(args.repo_root)}")
            stale += 1
    print(f"Checked freshness; flagged {stale} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
