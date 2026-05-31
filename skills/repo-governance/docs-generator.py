# skills/repo-governance/docs-generator.py
"""Documentation generation engine: Makefile, config, compose, k8s, rules, migrations."""

from __future__ import annotations

import argparse
import ast
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class DocTarget:
    name: str
    source_paths: list[str]
    output_path: str
    generator: Callable[[Path], str]
    description: str


@dataclass
class GenerationResult:
    target: str
    status: str
    diff_lines: int


def _header(source: str) -> str:
    return f"<!-- Generated from: {source} — do not edit manually -->\n\n"


def generate_makefile_doc(makefile_path: Path) -> str:
    text = makefile_path.read_text(encoding="utf-8")
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+([a-z0-9:-]+):\s*(.+)$", line, re.I)
        if m:
            rows.append((m.group(1), m.group(2).strip()))
    rows.sort(key=lambda x: x[0])
    lines = ["| Target | Description |", "|--------|-------------|"]
    for t, d in rows:
        lines.append(f"| `{t}` | {d} |")
    return _header(str(makefile_path)) + "## Make targets\n\n" + "\n".join(lines) + "\n"


def generate_env_vars_doc(config_path: Path) -> str:
    tree = ast.parse(config_path.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, str, str]] = []

    class V(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            bases = [getattr(b, "id", "") for b in node.bases if isinstance(b, ast.Name)]
            if "BaseSettings" in bases or any(
                isinstance(b, ast.Attribute) and b.attr == "BaseSettings" for b in node.bases
            ):
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        name = stmt.target.id
                        ann = ast.unparse(stmt.annotation) if stmt.annotation else ""
                        default = ""
                        desc = ""
                        if stmt.value is not None:
                            default = ast.unparse(stmt.value)[:60]
                        rows.append((name, ann, default, desc))
            self.generic_visit(node)

    V().visit(tree)
    lines = [
        _header(str(config_path)),
        "## Environment variables (from Settings)\n\n",
        "| Variable | Type | Default | Description |\n",
        "|----------|------|---------|-------------|\n",
    ]
    for name, ann, default, desc in rows:
        lines.append(f"| `{name}` | `{ann}` | {default} | {desc} |\n")
    return "".join(lines)


def generate_compose_doc(compose_path: Path) -> str:
    if yaml is None:
        return _header(str(compose_path)) + "_PyYAML not installed; run `pip install pyyaml`._\n"
    data = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
    services = data.get("services") or {}
    lines = [
        _header(str(compose_path)),
        "## Docker Compose services\n\n",
        "| Service | Image | Ports | Profiles |\n",
        "|---------|-------|-------|----------|\n",
    ]
    for sname, scfg in sorted(services.items()):
        if not isinstance(scfg, dict):
            continue
        img = str(scfg.get("image", ""))
        ports = scfg.get("ports") or []
        prof = ",".join(scfg.get("profiles") or []) or "-"
        port_s = str(ports)[:80]
        lines.append(f"| `{sname}` | {img} | {port_s} | {prof} |\n")
    return "".join(lines)


def generate_k8s_doc(k8s_base_path: Path) -> str:
    parts: list[str] = [_header(str(k8s_base_path)), "## Kubernetes resources\n\n"]
    for ypath in sorted(k8s_base_path.glob("*.yaml")):
        if yaml is None:
            parts.append(f"- `{ypath.name}` (install PyYAML for details)\n")
            continue
        doc = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "?")
        meta = doc.get("metadata") or {}
        name = meta.get("name", "?")
        parts.append(f"### {kind}/{name}\n\n```yaml\n# {ypath.name}\n```\n\n")
    return "".join(parts)


def generate_rules_index(rules_path: Path) -> str:
    lines = [
        _header(str(rules_path)),
        "## Cursor rules\n\n",
        "| Rule | Scope | Summary |\n",
        "|------|-------|--------|\n",
    ]
    for md in sorted(rules_path.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        summary = ""
        scope = ""
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                fm = text[3:end]
                for ln in fm.splitlines():
                    if ln.startswith("description:"):
                        summary = ln.split(":", 1)[1].strip()
                    if "alwaysApply" in ln and "true" in ln:
                        scope = "always"
                    if ln.strip().startswith("globs:"):
                        scope = "globs"
        if not summary:
            summary = (text[end + 3 : end + 200].strip() if end != -1 else text[:120]).split("\n")[0][:80]
        lines.append(f"| `{md.name}` | {scope or '-'} | {summary} |\n")
    return "".join(lines)


def generate_migration_history(versions_path: Path) -> str:
    lines = [
        _header(str(versions_path)),
        "## Alembic revisions\n\n",
        "| Revision | Down | Description |\n",
        "|----------|------|---------------|\n",
    ]
    for pyf in sorted(versions_path.glob("*.py")):
        if pyf.name.startswith("__"):
            continue
        text = pyf.read_text(encoding="utf-8")
        rev_m = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", text, re.M)
        down_m = re.search(r"^down_revision\s*=\s*['\"]([^'\"]*)['\"]|None", text, re.M)
        rev = rev_m.group(1) if rev_m else pyf.stem
        down = down_m.group(1) if down_m else "-"
        doc = ast.get_docstring(ast.parse(text)) or ""
        desc = doc.split("\n")[0][:80] if doc else ""
        lines.append(f"| `{rev}` | `{down}` | {desc} |\n")
    return "".join(lines)


def run_pipeline(
    mode: str,
    targets: list[DocTarget],
    repo_root: Path,
) -> list[GenerationResult]:
    results: list[GenerationResult] = []
    for t in targets:
        src = repo_root / t.source_paths[0]
        out = repo_root / t.output_path
        if not src.is_file() and not src.is_dir():
            results.append(GenerationResult(t.name, "skipped", 0))
            continue
        try:
            content = t.generator(src if src.is_file() else src)
        except OSError as exc:
            results.append(GenerationResult(t.name, f"error: {exc}", 0))
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        if mode == "generate":
            old = out.read_text(encoding="utf-8") if out.is_file() else ""
            out.write_text(content, encoding="utf-8")
            status = "unchanged" if old == content else "generated"
            diff = sum(1 for a, b in zip(old.splitlines(), content.splitlines()) if a != b)
            results.append(GenerationResult(t.name, status, diff))
        else:
            old = out.read_text(encoding="utf-8") if out.is_file() else ""
            if old != content:
                results.append(GenerationResult(t.name, "drifted", len(content.splitlines())))
            else:
                results.append(GenerationResult(t.name, "unchanged", 0))
    return results


def _default_targets(repo_root: Path) -> list[DocTarget]:
    return [
        DocTarget(
            "makefile",
            ["Makefile"],
            "docs/generated/make-targets.md",
            generate_makefile_doc,
            "Makefile help lines",
        ),
        DocTarget(
            "config",
            ["apps/api/app/core/config.py"],
            "docs/generated/settings-fields.md",
            generate_env_vars_doc,
            "Settings AST",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Documentation generation pipeline")
    parser.add_argument("--mode", choices=("generate", "check"), default="generate")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--target", default="", help="Optional target name")
    args = parser.parse_args()
    root = args.repo_root
    targets = _default_targets(root)
    extra = [
        DocTarget(
            "compose",
            ["compose.yml"],
            "docs/generated/compose.md",
            generate_compose_doc,
            "Compose file",
        ),
        DocTarget(
            "k8s",
            ["deploy/k8s/base"],
            "docs/generated/k8s-base.md",
            generate_k8s_doc,
            "K8s base",
        ),
        DocTarget(
            "rules",
            [".cursor/rules"],
            "docs/generated/cursor-rules.md",
            generate_rules_index,
            "Rules index",
        ),
        DocTarget(
            "migrations",
            ["apps/api/app/alembic/versions"],
            "docs/generated/migrations.md",
            generate_migration_history,
            "Alembic",
        ),
    ]
    targets.extend(extra)
    if args.target:
        targets = [t for t in targets if t.name == args.target]
    results = run_pipeline(args.mode, targets, root)
    drifted = False
    for r in results:
        print(f"{r.target}: {r.status} (lines changed ~{r.diff_lines})")
        if r.status == "drifted":
            drifted = True
    return 1 if (args.mode == "check" and drifted) else 0


if __name__ == "__main__":
    raise SystemExit(main())
