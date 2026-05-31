# skills/security/dependency-audit.py
"""Run pip-audit if installed."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    try:
        return subprocess.call([sys.executable, "-m", "pip_audit"])
    except FileNotFoundError:
        print("pip-audit not installed", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
