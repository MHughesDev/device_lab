# skills/agent-ops/handoff-template-generator.py
"""Emit a Markdown handoff skeleton from git status and optional queue id."""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def git_shortstat(repo: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), "diff", "--stat", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (r.stdout or "(no commits or not a git repo)").strip()


def load_queue_row(repo: Path, qid: str) -> dict[str, str] | None:
    path = repo / "queue" / "queue.csv"
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    start = 1 if lines and lines[0].startswith("#") else 0
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    for row in reader:
        if (row.get("id") or "").strip() == qid:
            return dict(row)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--queue-id", default="")
    args = parser.parse_args()
    repo = args.repo_root
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    stat = git_shortstat(repo)
    lines = [
        "# Handoff",
        "",
        f"**Generated:** {ts}",
        "",
        "## Git diff --stat",
        "",
        "```",
        stat,
        "```",
        "",
    ]
    if args.queue_id:
        row = load_queue_row(repo, args.queue_id)
        if row:
            lines += [
                "## Queue item",
                "",
                f"- **id:** {row.get('id', '')}",
                f"- **summary:** {row.get('summary', '')}",
                "",
            ]
        else:
            lines += ["## Queue item", "", f"(id {args.queue_id!r} not found)", ""]
    lines += [
        "## Commands run",
        "",
        "(paste make lint / make test output)",
        "",
        "## Risks",
        "",
        "- ",
        "",
        "## Follow-ups",
        "",
        "- ",
        "",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
