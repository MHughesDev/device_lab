# scripts/repo_self_audit.py
"""Comprehensive repository self-audit: paths, queue, skills, prompts, Makefile, titles."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REQUIRED_PATHS = (
    "AGENTS.md",
    "PYTHON_PROCEDURES.md",
    "Makefile",
    "pyproject.toml",
    ".gitignore",
    ".dockerignore",
    ".gitattributes",
    ".env.example",
    "compose.yml",
    "apps/api/Dockerfile",
    "apps/api/AGENTS.md",
    "apps/api/app/main.py",
    "apps/api/app/core/config.py",
    "apps/api/app/core/db.py",
    "apps/api/app/models.py",
    "apps/web/Dockerfile",
    "apps/web/AGENTS.md",
    "apps/web/package.json",
    "apps/web/src/main.tsx",
    "scripts/repo_self_audit.py",
    "scripts/queue_validate.py",
    "scripts/queue_archive.py",
    "queue/queue.csv",
    "queue/queuearchive.csv",
    "queue/QUEUE_INSTRUCTIONS.md",
    "queue/QUEUE_AGENT_PROMPT.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "README.md",
    ".github/workflows/ci.yml",
    ".github/workflows/cd.yml",
)

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache"}

# apps/api and apps/web are vendored from the upstream Tiangolo full-stack
# template; their source files keep upstream conventions and skip the
# template-systemization first-line-comment rule.
VENDORED_PREFIXES = (("apps", "api"), ("apps", "web"))
TITLE_EXT = {".py", ".md", ".sh", ".yml", ".yaml"}
SKILL_HEADINGS = ("purpose", "when to invoke", "prerequisites")


def run_queue_validate(root: Path) -> tuple[bool, str]:
    script = root / "scripts" / "queue_validate.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out.strip() or ("OK" if proc.returncode == 0 else "failed")


def check_required_files(root: Path) -> list[str]:
    missing: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (root / rel).is_file():
            missing.append(rel)
    return missing


def file_title_comments(root: Path) -> list[str]:
    bad: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            rel_parts = path.parts
        if any(rel_parts[: len(pref)] == pref for pref in VENDORED_PREFIXES):
            continue
        if path.suffix.lower() not in TITLE_EXT:
            continue
        if "prompts" in path.parts:
            continue
        if path.parts[0] == "docs" and "generated" in path.parts:
            continue
        if ".cursor" in path.parts or ".github" in path.parts:
            continue
        if "alembic" in path.parts and "versions" in path.parts:
            continue
        if path.suffix in {".yml", ".yaml"} and path.parts[0] not in (
            "apps",
            "packages",
            "deploy",
            ".github",
        ):
            continue
        if path.suffix == ".md" and "spec" in path.parts:
            continue
        try:
            first = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:3]
        except OSError:
            continue
        text = "\n".join(first).lower()
        ok = False
        if path.suffix == ".py" and first and first[0].startswith("#"):
            ok = "/" in first[0] or path.name in first[0]
        elif path.suffix == ".md" and first and (
            first[0].startswith("# ")
            or "<!--" in first[0]
            or first[0].strip() == "---"
        ):
            ok = True
        elif path.suffix in {".sh", ".yml", ".yaml"} and len(first) > 1:
            ok = first[0].startswith("#!") and (len(first) > 1 and first[1].startswith("#"))
        if not ok and first:
            bad.append(str(path.relative_to(root)))
    return bad


def skills_have_sections(root: Path) -> list[str]:
    bad: list[str] = []
    skills = root / "skills"
    for md in skills.rglob("*.md"):
        if md.name == "README.md":
            continue
        text = md.read_text(encoding="utf-8", errors="ignore").lower()
        has_purpose = "## purpose" in text or "**purpose:**" in text
        has_when = "when to invoke" in text
        has_pre = "prerequisites" in text
        if not (has_purpose and has_when and has_pre):
            bad.append(str(md.relative_to(root)))
    return bad


def prompts_have_frontmatter(root: Path) -> list[str]:
    bad: list[str] = []
    for md in (root / "prompts").glob("*.md"):
        if md.name == "README.md":
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        if not any(l.strip() == "---" for l in lines[:40]):
            bad.append(str(md.relative_to(root)))
    return bad


def check_prompt_frontmatter(root: Path) -> list[str]:
    """Verify prompt templates have a title line and YAML front matter with required fields."""

    errors: list[str] = []
    prompts_dir = root / "prompts"
    required_fields = ("purpose:", "when_to_use:")
    for md_file in sorted(prompts_dir.glob("*.md")):
        if md_file.name == "README.md":
            continue
        rel = md_file.relative_to(root)
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        first_line = content.splitlines()[0] if content.splitlines() else ""
        if not first_line.startswith(f"# prompts/{md_file.name}"):
            errors.append(f"{rel}: expected first line `# prompts/{md_file.name}`")
        if "---" not in content:
            errors.append(f"{rel}: missing YAML front matter")
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            errors.append(f"{rel}: malformed front matter")
            continue
        front_matter = parts[1]
        for field in required_fields:
            if field not in front_matter:
                errors.append(f"{rel}: missing front matter field '{field.rstrip(':')}'")
    return errors


def makefile_targets_documented(root: Path) -> list[str]:
    makefile = root / "Makefile"
    text = makefile.read_text(encoding="utf-8", errors="ignore")
    undocumented: list[str] = []
    for m in re.finditer(r"^([a-zA-Z][a-zA-Z0-9_\\:-]+):", text, re.MULTILINE):
        target = m.group(1).replace("\\", "")
        if target in {".PHONY", "help"}:
            continue
        if ":" in target:
            continue
        start = m.start()
        chunk = text[max(0, start - 200) : start]
        if not re.search(r"^##\s+" + re.escape(target) + r"\s*:", chunk, re.M):
            undocumented.append(target)
    return undocumented[:50]


def main() -> int:
    parser = argparse.ArgumentParser(description="Repository self-audit")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args()
    root: Path = args.repo_root
    sections: list[tuple[str, bool, list[str]]] = []

    missing = check_required_files(root)
    sections.append(("required_files", len(missing) == 0, missing))

    ok_q, msg_q = run_queue_validate(root)
    sections.append(("queue_validate", ok_q, [] if ok_q else [msg_q]))

    titles = file_title_comments(root)
    sections.append(("file_title_comments", len(titles) == 0, titles[:30]))

    skills = skills_have_sections(root)
    sections.append(("skills_headings", len(skills) == 0, skills[:20]))

    prompts = prompts_have_frontmatter(root)
    sections.append(("prompts_frontmatter", len(prompts) == 0, prompts))

    prompt_fields = check_prompt_frontmatter(root)
    sections.append(("prompts_title_and_fields", len(prompt_fields) == 0, prompt_fields))

    mk = makefile_targets_documented(root)
    sections.append(("makefile_help", len(mk) == 0, mk))

    blocking = any(not ok for _, ok, _ in sections)

    print("# Repository self-audit\n")
    for name, ok, items in sections:
        status = "PASS" if ok else "FAIL"
        print(f"## {name}: {status}")
        for it in items[:25]:
            print(f"  - {it}")
        print()

    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
