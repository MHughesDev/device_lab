#!/usr/bin/env python3
"""Rename the template baseline for a newly cloned product repository."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Replacement:
    path: Path
    description: str
    original: str
    updated: str


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "new-product"


def _title(value: str) -> str:
    words = re.split(r"[-_\s]+", value.strip())
    return " ".join(word[:1].upper() + word[1:] for word in words if word)


def _replace_line(text: str, prefix: str, value: str) -> str:
    return re.sub(rf"^({re.escape(prefix)}).*?$", rf"\g<1>{value}", text, flags=re.MULTILINE)


def _replace_pyproject_name(text: str, project_slug: str) -> str:
    return re.sub(
        r'(?m)^(name\s*=\s*")[^"]+(")$',
        rf"\g<1>{project_slug}\2",
        text,
        count=1,
    )


def _replace_json_name(text: str, project_slug: str) -> str:
    return re.sub(
        r'(?m)^(\s*"name"\s*:\s*")[^"]+(")',
        rf"\g<1>{project_slug}\2",
        text,
        count=1,
    )


def build_replacements(
    root: Path,
    *,
    project_name: str,
    system_name: str,
    mission: str,
    archetype: str,
    profiles: str,
    contexts: str,
) -> list[Replacement]:
    project_slug = _slugify(project_name)
    system = system_name.strip() or _title(project_slug)
    one_line = mission.strip() or f"Build and operate {system}."
    replacements: list[Replacement] = []

    agents = root / "AGENTS.md"
    if agents.exists():
        original = agents.read_text(encoding="utf-8")
        updated = original
        updated = _replace_line(updated, "- **System name:** ", system)
        updated = _replace_line(updated, "- **One-line mission:** ", one_line)
        updated = _replace_line(updated, "- **Archetype:** ", archetype)
        updated = _replace_line(updated, "- **Active profiles:** ", profiles)
        updated = _replace_line(updated, "- **Primary bounded contexts:** ", contexts)
        updated = updated.replace("_populate during initialization_", system)
        replacements.append(Replacement(agents, "AGENTS.md mission block", original, updated))

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        original = pyproject.read_text(encoding="utf-8")
        updated = _replace_pyproject_name(original, project_slug)
        updated = updated.replace("full-stack template", f"full-stack {project_slug}")
        replacements.append(Replacement(pyproject, "root pyproject project name", original, updated))

    package_json = root / "package.json"
    if package_json.exists():
        original = package_json.read_text(encoding="utf-8")
        updated = _replace_json_name(original, f"{project_slug}-fullstack")
        replacements.append(Replacement(package_json, "root package.json package name", original, updated))

    readme = root / "README.md"
    if readme.exists():
        original = readme.read_text(encoding="utf-8")
        updated = original.replace(
            "# 🏗️ The Software Factory: Your AI-First Launchpad 🚀",
            f"# {system}",
        )
        updated = updated.replace(
            "Welcome to the **Software Factory**.",
            f"Welcome to **{system}**.",
        )
        replacements.append(Replacement(readme, "README title and product name", original, updated))

    return replacements


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename this template for a newly cloned product repository.",
    )
    parser.add_argument("project_name", help="Product slug or display name, e.g. acme-portal")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--system-name", default="", help="Display name for AGENTS.md and README")
    parser.add_argument("--mission", default="", help="One-line mission for AGENTS.md")
    parser.add_argument("--archetype", default="full-stack modular monolith")
    parser.add_argument("--profiles", default="api, web")
    parser.add_argument("--contexts", default="auth, users, core")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    replacements = build_replacements(
        root,
        project_name=args.project_name,
        system_name=args.system_name,
        mission=args.mission,
        archetype=args.archetype,
        profiles=args.profiles,
        contexts=args.contexts,
    )

    changed = [item for item in replacements if item.original != item.updated]
    if not changed:
        print("rename-from-template: no changes needed")
        return 0

    for item in changed:
        rel = item.path.relative_to(root)
        print(f"{rel}: {item.description}")
        if not args.dry_run:
            item.path.write_text(item.updated, encoding="utf-8")

    if args.dry_run:
        print(f"rename-from-template: dry run complete ({len(changed)} file(s) would change)")
    else:
        print(f"rename-from-template: updated {len(changed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
