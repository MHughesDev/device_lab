# skills/backend/openapi-diff.py
"""Fetch OpenAPI JSON from a running API and compare path keys to previous file."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def fetch_schema(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def path_set(spec: dict[str, object]) -> set[str]:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return set()
    return set(paths.keys())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/openapi.json")
    parser.add_argument("--baseline", type=Path, default=Path("docs/api/openapi-baseline.json"))
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()
    try:
        spec = fetch_schema(args.url)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"Could not fetch schema: {exc}", file=sys.stderr)
        return 1
    if args.write_baseline:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.baseline}")
        return 0
    if not args.baseline.is_file():
        print("No baseline — run with --write-baseline while API is up.", file=sys.stderr)
        return 1
    old = json.loads(args.baseline.read_text(encoding="utf-8"))
    p_old, p_new = path_set(old), path_set(spec)
    added = sorted(p_new - p_old)
    removed = sorted(p_old - p_new)
    if added:
        print("Added paths:", ", ".join(added))
    if removed:
        print("Removed paths:", ", ".join(removed))
    if not added and not removed:
        print("OpenAPI paths unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
