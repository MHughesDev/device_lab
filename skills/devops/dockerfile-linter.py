# skills/devops/dockerfile-linter.py
"""Basic Dockerfile checks: FROM, USER, HEALTHCHECK."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dockerfile", type=Path, nargs="?", default=Path("apps/api/Dockerfile"))
    args = parser.parse_args()
    if not args.dockerfile.is_file():
        print("Dockerfile not found", file=sys.stderr)
        return 1
    text = args.dockerfile.read_text(encoding="utf-8")
    issues = 0
    if "FROM " not in text:
        print("Missing FROM")
        issues += 1
    if "USER " not in text:
        print("Warning: no USER directive")
    if "HEALTHCHECK" not in text:
        print("Warning: no HEALTHCHECK")
    return min(issues, 1)


if __name__ == "__main__":
    raise SystemExit(main())
