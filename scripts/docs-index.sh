#!/usr/bin/env bash
# scripts/docs-index.sh
# Manual human/AI-agent helper: propose a docs index update on demand, never from CI.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Building a human/AI-agent maintained docs index suggestion..."
export REPO_ROOT="$ROOT"
python3 <<'PY'
from __future__ import annotations

import os
from pathlib import Path

root = Path(os.environ["REPO_ROOT"]) / "docs"
readme = root / "README.md"
lines = [
    "## Maintained docs index",
    "",
    "_Review this generated suggestion before committing; CI must not run this script._",
    "",
]
for d in sorted(root.iterdir()):
    if d.name.startswith(".") or d.name == "README.md":
        continue
    if d.is_dir():
        sub = d / "README.md"
        if sub.exists():
            lines.append(f"- [{d.name}/]({d.name}/README.md)")
        else:
            lines.append(f"- `{d.name}/`")
    elif d.is_file() and d.suffix == ".md":
        lines.append(f"- [{d.stem}]({d.name})")
lines.append("")
block = "\n".join(lines) + "\n"

if not readme.is_file():
    readme.write_text("# docs/README.md\n\n" + block, encoding="utf-8")
    print(f"Created {readme}")
else:
    text = readme.read_text(encoding="utf-8")
    new_text = text.rstrip() + "\n\n" + block + "\n"
    readme.write_text(new_text, encoding="utf-8")
    print(f"Updated {readme}")
PY
echo "Done."
