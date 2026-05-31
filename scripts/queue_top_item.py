# scripts/queue_top_item.py
"""Print the first open, non-human-ops queue row as one line (JSON) for agents."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.queue_ops import OPEN_FIELDS, HUMAN_OPS_CATEGORY, load_open_rows


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    path = root / "queue" / "queue.csv"
    if not path.is_file():
        err = {"error": "missing_file", "path": "queue/queue.csv"}
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        return 1
    try:
        rows = load_open_rows(path)
    except ValueError as e:
        err = {"error": "invalid_csv", "detail": str(e)}
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        return 1

    for row in rows:
        if row.get("category", "").strip().lower() == HUMAN_OPS_CATEGORY:
            continue
        item = {k: (row.get(k) or "").strip() for k in OPEN_FIELDS}
        print(json.dumps(item, ensure_ascii=False))
        return 0

    empty = {"error": "no_open_items", "message": "queue.csv has no non-human-ops data rows"}
    print(json.dumps(empty, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
