# skills/repo-governance/rule-linter.py
"""Validate .cursor/rules/*.md YAML front matter and glob syntax."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint Cursor rule files")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    rules = args.repo_root / ".cursor" / "rules"
    if not rules.is_dir():
        print("No .cursor/rules", file=sys.stderr)
        return 1
    err = 0
    for f in sorted(rules.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            print(f"Missing YAML front matter start: {f}", file=sys.stderr)
            err += 1
            continue
        try:
            end = lines.index("---", 1)
        except ValueError:
            print(f"Missing closing --- in front matter: {f}", file=sys.stderr)
            err += 1
            continue
        fm = "\n".join(lines[1:end])
        if "alwaysApply" not in fm and "globs:" not in fm:
            print(
                f"{f}: front matter should set alwaysApply or globs",
                file=sys.stderr,
            )
            err += 1
        for ln in fm.splitlines():
            m = re.match(r"^\s*globs:\s*(.+)$", ln)
            if m:
                pat = m.group(1).strip()
                if pat.startswith("[") and pat.endswith("]"):
                    continue
                if not pat or pat in {"-", "null"}:
                    print(f"{f}: empty globs entry", file=sys.stderr)
                    err += 1
    return min(err, 255)


if __name__ == "__main__":
    raise SystemExit(main())
