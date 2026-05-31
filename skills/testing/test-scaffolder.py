# skills/testing/test-scaffolder.py
"""Emit pytest stub tests for each @router.* route in apps/api/app/<module>/router.py."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def find_routes(source: str) -> list[tuple[str, str]]:
    """Return (method, path) from FastAPI route decorators."""

    out: list[tuple[str, str]] = []
    for m in re.finditer(
        r"@router\.(get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']",
        source,
    ):
        out.append((m.group(1).upper(), m.group(2)))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate pytest stub tests for a router module")
    parser.add_argument("--module", required=True, help="Bounded context name under apps/api/app/")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    router_file = args.repo_root / "apps" / "api" / "src" / args.module / "router.py"
    if not router_file.is_file():
        print(f"Router not found: {router_file}", file=sys.stderr)
        return 1
    text = router_file.read_text(encoding="utf-8")
    routes = find_routes(text)
    mod = args.module
    print(f'"""Generated stubs for {mod}."""')
    print()
    print("import pytest")
    print()
    for method, path in routes:
        safe = path.replace("/", "_").replace("{", "").replace("}", "").strip("_") or "root"
        fname = f"test_{mod}_{method.lower()}_{safe}"
        print()
        print(f"async def {fname}() -> None:")
        print(f'    raise NotImplementedError("{method} {path}")')
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
