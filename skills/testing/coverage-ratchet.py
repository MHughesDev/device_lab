# skills/testing/coverage-ratchet.py
"""Read coverage.xml and compare to floor in docs/quality/coverage-policy.md or --min."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def floor_from_policy(policy_path: Path) -> float | None:
    if not policy_path.is_file():
        return None
    text = policy_path.read_text(encoding="utf-8")
    m = re.search(r"<!--\s*coverage-floor:\s*([\d.]+)\s*-->", text)
    if m:
        return float(m.group(1))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Coverage floor check / ratchet")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--xml", type=Path, default=Path("coverage.xml"))
    parser.add_argument("--min", type=float, default=0.0, dest="min_cov")
    parser.add_argument(
        "--update-policy",
        action="store_true",
        help="If coverage exceeds floor, update coverage-floor comment in coverage-policy.md",
    )
    args = parser.parse_args()
    xml_path = args.repo_root / args.xml if not args.xml.is_absolute() else args.xml
    if not xml_path.is_file():
        print(f"Missing {xml_path} — run pytest with coverage first.", file=sys.stderr)
        return 1

    policy = args.repo_root / "docs" / "quality" / "coverage-policy.md"
    floor = args.min_cov
    if floor <= 0:
        parsed = floor_from_policy(policy)
        if parsed is not None:
            floor = parsed
        else:
            floor = 55.0

    tree = ET.parse(xml_path)
    root = tree.getroot()
    rate = float(root.attrib.get("line-rate", "0")) * 100
    print(f"Total line coverage: {rate:.2f}% (floor {floor:.2f}%)")

    if rate < floor:
        print(f"Below floor {floor}%", file=sys.stderr)
        return 1

    if args.update_policy and policy.is_file():
        text = policy.read_text(encoding="utf-8")
        new_floor = round(rate, 2)
        if re.search(r"<!--\s*coverage-floor:", text):
            new_text = re.sub(
                r"<!--\s*coverage-floor:\s*[\d.]+\s*-->",
                f"<!-- coverage-floor: {new_floor} -->",
                text,
                count=1,
            )
            if new_text != text:
                policy.write_text(new_text, encoding="utf-8")
                print(f"Updated coverage policy floor to {new_floor}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
