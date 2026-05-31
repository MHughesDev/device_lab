#!/usr/bin/env python3
"""Convert blueprint-style blockquotes (> PURPOSE: / > CONTENT:) to normal Markdown.

Scans repository Markdown files (excluding spec/) and rewrites lines so that:
- `> PURPOSE: ...` becomes `**Purpose:** ...`
- `> CONTENT:` blocks become plain paragraphs/lists without the blockquote prefix.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIR_NAMES = {"spec", ".git", "node_modules", ".venv"}


def convert_lines(raw_lines: list[str]) -> list[str]:
    """Input: lines without trailing newlines."""
    out: list[str] = []
    i = 0
    n = len(raw_lines)

    def is_content_continuation(line: str) -> bool:
        if not line.startswith(">"):
            return False
        stripped = line[1:].lstrip()
        if stripped.startswith("PURPOSE:") or stripped.startswith("CONTENT:"):
            return False
        return True

    while i < n:
        line = raw_lines[i]
        if line.startswith("> PURPOSE:"):
            rest = line[len("> PURPOSE:") :].strip()
            out.append(f"**Purpose:** {rest}" if rest else "**Purpose:**")
            i += 1
            continue
        if line.startswith("> CONTENT:"):
            rest = line[len("> CONTENT:") :].strip()
            if rest:
                out.append(rest)
            i += 1
            while i < n and is_content_continuation(raw_lines[i]):
                cont = raw_lines[i]
                if cont.startswith("> "):
                    out.append(cont[2:])
                elif cont == ">":
                    out.append("")
                elif cont.startswith(">"):
                    out.append(cont[1:].lstrip())
                else:
                    out.append(cont)
                i += 1
            continue
        out.append(line)
        i += 1
    return out


def should_process(path: Path) -> bool:
    if path.suffix.lower() != ".md":
        return False
    return not any(p in EXCLUDE_DIR_NAMES for p in path.parts)


def main() -> int:
    changed = 0
    for md in sorted(ROOT.rglob("*.md")):
        if not should_process(md):
            continue
        text = md.read_text(encoding="utf-8")
        if "> PURPOSE:" not in text and "> CONTENT:" not in text:
            continue
        raw_lines = text.splitlines()
        new_lines = convert_lines(raw_lines)
        new_text = "\n".join(new_lines)
        if text.endswith("\n"):
            new_text += "\n"
        if new_text != text:
            md.write_text(new_text, encoding="utf-8")
            changed += 1
            print(md.relative_to(ROOT))
    print(f"Updated {changed} files.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
