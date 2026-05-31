#!/usr/bin/env python3
"""Scan for residual template tokens and print a replacement plan."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATHS = [
    ".env.example",
    "compose.yml",
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    "package.json",
    "apps/web/package.json",
]
TOKEN_RE = re.compile(
    r"template(?:[-_][a-z0-9]+)*|Template(?:[-_ ][A-Za-z0-9]+)*|TEMPLATE(?:[-_][A-Z0-9]+)*|"
    r"_populate during initialization_|STACK_NAME|SENTRY_DSN|namespace",
)


@dataclass(frozen=True)
class Match:
    path: Path
    line_number: int
    line: str
    token: str
    suggestion: str


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "new-product"


def _suggest(token: str, project_slug: str) -> str:
    if token == "template":
        return project_slug
    if token.startswith("template-"):
        return token.replace("template", project_slug, 1)
    if token == "Template":
        return project_slug.replace("-", " ").title()
    if token.startswith("Template"):
        return token.replace("Template", project_slug.replace("-", " ").title(), 1)
    if token == "TEMPLATE":
        return project_slug.upper().replace("-", "_")
    if token.startswith("TEMPLATE_"):
        return token.replace("TEMPLATE", project_slug.upper().replace("-", "_"), 1)
    if token == "_populate during initialization_":
        return "<fill during repo initialization>"
    if token == "STACK_NAME":
        return f"STACK_NAME={project_slug}-fullstack"
    if token == "SENTRY_DSN":
        return "SENTRY_DSN=<project-specific DSN or blank>"
    if token == "namespace":
        return f"namespace={project_slug}"
    return project_slug


def scan(root: Path, project_name: str, paths: list[str]) -> list[Match]:
    project_slug = _slugify(project_name)
    matches: list[Match] = []
    for raw_path in paths:
        path = root / raw_path
        if not path.exists() or not path.is_file():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            for found in TOKEN_RE.finditer(line):
                token = found.group(0)
                matches.append(
                    Match(
                        path=path,
                        line_number=line_number,
                        line=line.rstrip(),
                        token=token,
                        suggestion=_suggest(token, project_slug),
                    ),
                )
    return matches


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report residual template tokens and suggested replacements for a new product.",
    )
    parser.add_argument("project_name", nargs="?", default="new-product", help="Desired project slug/name")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--fail-on-found", action="store_true", help="Exit 1 when matches are found")
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Additional or replacement path to scan; repeatable. Defaults to known template files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    paths = args.paths if args.paths else DEFAULT_PATHS
    matches = scan(root, args.project_name, paths)
    if not matches:
        print("template_token_sweep: no residual template tokens found")
        return 0

    print(f"template_token_sweep: {len(matches)} match(es) found")
    for match in matches:
        rel = match.path.relative_to(root)
        print(f"{rel}:{match.line_number}: token={match.token!r} -> suggestion={match.suggestion!r}")
        print(f"  {match.line}")
    return 1 if args.fail_on_found else 0


if __name__ == "__main__":
    raise SystemExit(main())
