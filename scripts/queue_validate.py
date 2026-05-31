# scripts/queue_validate.py
"""Validate queue/queue.csv and queue/queuearchive.csv schema and invariants."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.queue_ops import validate_archive, validate_open


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    q_open = root / "queue" / "queue.csv"
    q_arch = root / "queue" / "queuearchive.csv"
    errs: list[str] = []
    errs.extend(validate_open(q_open))
    errs.extend(validate_archive(q_arch))
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    print("Queue OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
