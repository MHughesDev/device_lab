# skills/repo-governance/adr-index-generator.py
"""Write docs/adr/README.md with a table of ADR files (excluding template)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ADR index")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    adr = args.repo_root / "docs" / "adr"
    if not adr.is_dir():
        print("No docs/adr", file=sys.stderr)
        return 1
    files = sorted(
        p for p in adr.glob("*.md") if p.name not in {"README.md", "template.md"}
    )
    lines = [
        "# ADR index\n",
        "\n",
        "_Auto-generated — run `make adr-index` to refresh._\n",
        "\n",
        "| ADR | Title | Status | Date |\n",
        "|-----|-------|--------|------|\n",
    ]
    for p in files:
        text = p.read_text(encoding="utf-8")
        title = ""
        status = ""
        date = ""
        for ln in text.splitlines()[:40]:
            if ln.startswith("# ") and not title:
                title = ln[2:].strip()
            m = re.match(r"^\*\*Status\*\*:\s*(.+)$", ln.strip())
            if m:
                status = m.group(1).strip()
            m = re.match(r"^\*\*Date\*\*:\s*(.+)$", ln.strip())
            if m:
                date = m.group(1).strip()
        if not title:
            title = p.stem
        rel = p.relative_to(args.repo_root).as_posix()
        lines.append(
            f"| [{p.stem}]({rel}) | {title} | {status or '-'} | {date or '-'} |\n"
        )
    out = adr / "README.md"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
