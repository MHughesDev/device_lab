# skills/backend/env-var-sync.py
"""Compare .env.example with Settings fields and env references in Python sources."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

SKIP_DIRS = {".venv", "node_modules", "__pycache__", ".git", "alembic"}


def env_var_names_from_example(text: str) -> set[str]:
    names: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Z][A-Z0-9_]*)\s*=", line)
        if m:
            names.add(m.group(1))
    return names


def field_names_from_config(text: str) -> set[str]:
    names: set[str] = set()
    for m in re.finditer(r"^\s+([a-z_][a-z0-9_]*)\s*:", text, re.MULTILINE):
        names.add(m.group(1))
    return names


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def env_refs_from_ast(tree: ast.AST) -> set[str]:
    """Collect env var names from os.getenv, os.environ[...], os.environ.get."""

    found: set[str] = set()

    class V(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "getenv" and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "os" and node.args:
                        s = _literal_string(node.args[0])
                        if s:
                            found.add(s)
                if node.func.attr == "get" and isinstance(node.func.value, ast.Attribute):
                    if (
                        node.func.value.attr == "environ"
                        and isinstance(node.func.value.value, ast.Name)
                        and node.func.value.value.id == "os"
                        and node.args
                    ):
                        s = _literal_string(node.args[0])
                        if s:
                            found.add(s)
            self.generic_visit(node)

        def visit_Subscript(self, node: ast.Subscript) -> None:
            if isinstance(node.value, ast.Attribute):
                if (
                    node.value.attr == "environ"
                    and isinstance(node.value.value, ast.Name)
                    and node.value.value.id == "os"
                ):
                    s = _literal_string(node.slice)
                    if s:
                        found.add(s)
            self.generic_visit(node)

    V().visit(tree)
    return found


def scan_python_for_env_usage(repo_root: Path) -> set[str]:
    """Scan apps/ and packages/ for dynamic env access."""

    roots = [repo_root / "apps", repo_root / "packages"]
    refs: set[str] = set()
    for base in roots:
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if any(p in path.parts for p in SKIP_DIRS):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            refs |= env_refs_from_ast(tree)
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare .env.example with Settings and os.getenv usage",
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.repo_root
    ex = root / ".env.example"
    cfg = root / "apps" / "api" / "src" / "config.py"
    if not ex.is_file() or not cfg.is_file():
        print("Missing .env.example or config.py", file=sys.stderr)
        return 1
    env_keys = env_var_names_from_example(ex.read_text(encoding="utf-8"))
    settings_fields = field_names_from_config(cfg.read_text(encoding="utf-8"))
    expected_upper = {f.upper() for f in settings_fields if f != "model_config"}
    missing = sorted(expected_upper - env_keys)
    extra = sorted(env_keys - expected_upper)
    if missing:
        print("In Settings but not in .env.example:", ", ".join(missing))
    if extra:
        print("In .env.example but not detected from config.py:", ", ".join(extra))

    code_refs = scan_python_for_env_usage(root)
    # Heuristic: code using getenv for vars not in .env.example
    orphan_code = sorted(code_refs - env_keys)
    if orphan_code:
        print("os.getenv/os.environ references not listed in .env.example:", ", ".join(orphan_code))

    if not missing and not extra and not orphan_code:
        print("env sync OK (Settings, .env.example, and getenv scan).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
