# skills/agent-ops/repo-self-audit.py
"""Thin wrapper: run the repository self-audit (see scripts/repo_self_audit.py)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repo self-audit")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    script = args.repo_root / "scripts" / "repo_self_audit.py"
    return subprocess.call([sys.executable, str(script), "--repo-root", str(args.repo_root)])


if __name__ == "__main__":
    raise SystemExit(main())
