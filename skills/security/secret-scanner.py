# skills/security/secret-scanner.py
"""Scan text files for common secret patterns and risky literals (informational)."""

from __future__ import annotations

import argparse
import math
import re
import subprocess
from pathlib import Path

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("openai_sk", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("pem_private", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("password_assign", re.compile(r"(?i)(password|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]")),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
]


def tracked_files(repo: Path) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(repo), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    ent = 0.0
    ln = len(s)
    for c in freq.values():
        p = c / ln
        ent -= p * math.log2(p)
    return ent


def scan_file(path: Path, rel: str, min_entropy: float) -> list[str]:
    hits: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return hits
    for i, line in enumerate(lines, start=1):
        for name, pat in PATTERNS:
            if pat.search(line):
                hits.append(f"{rel}:{i}: pattern:{name}: {line.strip()[:120]}")
        for m in re.finditer(r'"([A-Za-z0-9+/=]{32,})"', line):
            chunk = m.group(1)
            if shannon_entropy(chunk) >= min_entropy:
                hits.append(f"{rel}:{i}: high_entropy:{chunk[:20]}...")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Heuristic secret scan (informational)")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--min-entropy",
        type=float,
        default=4.2,
        help="Min Shannon entropy for quoted long strings",
    )
    args = parser.parse_args()
    exts = {".py", ".md", ".yml", ".yaml", ".sh", ".toml", ".json"}
    all_hits: list[str] = []
    for rel in tracked_files(args.repo_root):
        if not any(rel.endswith(e) for e in exts):
            continue
        path = args.repo_root / rel
        if not path.is_file():
            continue
        all_hits.extend(scan_file(path, rel, args.min_entropy))

    for h in all_hits:
        print(h)
    print(f"Done. Findings: {len(all_hits)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
