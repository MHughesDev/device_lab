# scripts/queue_archive.py
"""Move a queue row from queue.csv to queuearchive.csv and emit audit metrics."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

OPEN_FIELDS = [
    "id",
    "batch",
    "phase",
    "category",
    "complexity",
    "goal",
    "acceptance_criteria",
    "scope_boundary",
    "agent_instructions",
    "constraints",
    "context_files",
    "touch_files",
    "verification_cmds",
    "dependencies",
    "notes",
    "created_date",
]
ARCHIVE_FIELDS = OPEN_FIELDS + ["status", "completed_date"]


def _load_queue(path: Path) -> tuple[str, list[dict[str, str]]]:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    comment = ""
    start = 0
    if lines and lines[0].startswith("#"):
        comment = lines[0] + "\n"
        start = 1
    body = "\n".join(lines[start:])
    reader = csv.DictReader(io.StringIO(body))
    if list(reader.fieldnames or []) != OPEN_FIELDS:
        msg = f"{path}: expected columns {OPEN_FIELDS}, got {reader.fieldnames}"
        raise ValueError(msg)
    return comment, list(reader)


def _write_queue(path: Path, comment: str, rows: list[dict[str, str]]) -> None:
    buf = io.StringIO()
    if comment:
        buf.write(comment)
    writer = csv.DictWriter(buf, fieldnames=OPEN_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def archive_by_id(root: Path, queue_id: str, *, status: str = "done") -> int:
    """Remove the row with ``queue_id`` from queue.csv and append to queuearchive.csv."""

    q_path = root / "queue" / "queue.csv"
    a_path = root / "queue" / "queuearchive.csv"

    try:
        comment, rows = _load_queue(q_path)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    found: dict[str, str] | None = None
    kept: list[dict[str, str]] = []
    for row in rows:
        if row.get("id") == queue_id:
            found = row
        else:
            kept.append(row)

    if found is None:
        print(f"id {queue_id!r} not found in queue.csv", file=sys.stderr)
        return 1

    _write_queue(q_path, comment, kept)

    arch_row = {k: found.get(k, "") for k in OPEN_FIELDS}
    arch_row["status"] = status
    arch_row["completed_date"] = date.today().isoformat()

    a_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = a_path.exists() and a_path.stat().st_size > 0
    with a_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ARCHIVE_FIELDS)
        if not file_exists:
            handle.write("# queue/queuearchive.csv\n")
            writer.writeheader()
        writer.writerow(arch_row)

    print(f"Archived {queue_id}")

    # Emit audit metrics
    _emit_audit_metrics(root, found, status)

    return 0


def _extract_pr_url(notes: str) -> str | None:
    """Extract PR URL from notes field."""
    if not notes:
        return None
    # Match GitHub PR URLs
    pr_match = re.search(r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+", notes)
    if pr_match:
        return pr_match.group(0)
    return None


def _count_review_rounds(pr_url: str | None) -> int | None:
    """Best-effort count of review rounds from gh CLI."""
    if not pr_url:
        return None
    try:
        # Extract PR number from URL
        pr_match = re.search(r"/pull/(\d+)$", pr_url)
        if not pr_match:
            return None
        pr_number = pr_match.group(1)

        # Run gh pr view to get review information
        result = subprocess.run(
            ["gh", "pr", "view", pr_number, "--json", "reviews"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        reviews = data.get("reviews", [])

        # Count unique review rounds (grouped by reviewer + state changes)
        review_states = set()
        for review in reviews:
            reviewer = review.get("author", {}).get("login", "unknown")
            state = review.get("state", "")
            review_states.add((reviewer, state))

        return len(review_states) if review_states else None
    except Exception:
        return None


def _emit_audit_metrics(root: Path, row: dict[str, str], status: str) -> None:
    """Append JSON metrics line to queue/audit.log."""
    audit_log = root / "queue" / "audit.log"

    queue_id = row.get("id", "")
    batch = row.get("batch", "")
    complexity = row.get("complexity", "")
    notes = row.get("notes", "")
    created_date = row.get("created_date", "")

    # Extract PR URL from notes
    pr_url = _extract_pr_url(notes)

    # Calculate review rounds (best effort)
    review_rounds = _count_review_rounds(pr_url)

    # Build metrics record
    metrics: dict[str, Any] = {
        "queue_id": queue_id,
        "batch": batch,
        "complexity": complexity,
        "status": status,
        "branch_created_at": created_date if created_date else None,
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "pr_url": pr_url,
        "review_rounds": review_rounds,
    }

    # Append to audit log
    audit_log.parent.mkdir(parents=True, exist_ok=True)
    with audit_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive a queue row: by id, or --top for the first open row",
    )
    parser.add_argument(
        "queue_id",
        nargs="?",
        default=None,
        help="Queue item id (e.g. Q-001). Omit when using --top.",
    )
    parser.add_argument(
        "--top",
        action="store_true",
        help="Archive the first data row in queue.csv (active single-lane item).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args()
    root = args.root
    q_path = root / "queue" / "queue.csv"

    if args.top and args.queue_id:
        print("Use either QUEUE_ID or --top, not both.", file=sys.stderr)
        return 2
    if not args.top and not args.queue_id:
        print(
            "Usage: queue_archive.py <QUEUE_ID> [--root PATH]\n"
            "       queue_archive.py --top [--root PATH]\n"
            "  --top  Archive the top (first) open row — no id to paste.",
            file=sys.stderr,
        )
        return 2

    target_id = args.queue_id
    if args.top:
        try:
            _comment, rows = _load_queue(q_path)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        if not rows:
            print("queue.csv has no data rows to archive.", file=sys.stderr)
            return 1
        target_id = (rows[0].get("id") or "").strip()
        if not target_id:
            print("Top queue row has empty id.", file=sys.stderr)
            return 1

    if not target_id:
        print("No queue id resolved.", file=sys.stderr)
        return 2
    return archive_by_id(root, target_id)


if __name__ == "__main__":
    raise SystemExit(main())
