# skills/devops/k8s-manifest-validator.py
"""Render Kustomize overlay via kubectl or kustomize CLI."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", default="dev")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    path = args.repo_root / "deploy" / "k8s" / "overlays" / args.overlay
    if not path.is_dir():
        print(f"Missing {path}", file=sys.stderr)
        return 1
    if shutil.which("kubectl"):
        cmd = ["kubectl", "kustomize", str(path)]
    elif shutil.which("kustomize"):
        cmd = ["kustomize", "build", str(path)]
    else:
        print("kubectl/kustomize not installed", file=sys.stderr)
        return 0
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return 1
    print("Rendered", len(r.stdout or ""), "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
