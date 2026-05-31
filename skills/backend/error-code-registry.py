# skills/backend/error-code-registry.py
"""List member names of class ErrorCode in packages/contracts/errors.py."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    path = args.repo_root / "packages" / "contracts" / "errors.py"
    if not path.is_file():
        print(f"Missing {path}", file=sys.stderr)
        return 1
    tree = ast.parse(path.read_text(encoding="utf-8"))
    members: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ErrorCode":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id.isupper():
                            members.append(t.id)
    for m in sorted(members):
        print(m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
