# skills/testing/flaky-detector.py
"""Run pytest multiple times and report tests with mixed outcomes (flaky detection).

Uses --junit-xml for per-test tracking so individual flaky tests are named,
not just suite-level pass/fail.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def _run_pytest(path: str, repo_root: Path, junit_xml: str) -> int:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            path,
            "-q",
            "--tb=no",
            f"--junit-xml={junit_xml}",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    return result.returncode


def _parse_junit(xml_path: str) -> dict[str, bool]:
    """Return {test_node_id: passed} from a JUnit XML file."""
    outcomes: dict[str, bool] = {}
    try:
        tree = ET.parse(xml_path)
    except (ET.ParseError, FileNotFoundError):
        return outcomes
    for tc in tree.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        node_id = f"{classname}::{name}" if classname else name
        failed = tc.find("failure") is not None or tc.find("error") is not None
        skipped = tc.find("skipped") is not None
        if not skipped:
            outcomes[node_id] = not failed
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect flaky tests by running pytest N times and comparing per-test outcomes."
    )
    parser.add_argument("--runs", type=int, default=3, help="Number of pytest runs (default: 3)")
    parser.add_argument("--path", default="apps/api/tests", help="Test path to pass to pytest")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args()

    # test_id -> list[bool] (True=passed, False=failed)
    all_outcomes: dict[str, list[bool]] = defaultdict(list)

    with tempfile.TemporaryDirectory() as tmpdir:
        for run_idx in range(args.runs):
            xml_path = str(Path(tmpdir) / f"junit_{run_idx}.xml")
            _run_pytest(args.path, args.repo_root, xml_path)
            run_outcomes = _parse_junit(xml_path)
            if not run_outcomes:
                # Fallback: no XML produced (e.g. no tests collected)
                print(f"Run {run_idx + 1}: no test results parsed (check path or pytest install)")
                continue
            for node_id, passed in run_outcomes.items():
                all_outcomes[node_id].append(passed)
            total = len(run_outcomes)
            passed_count = sum(1 for v in run_outcomes.values() if v)
            print(f"Run {run_idx + 1}: {passed_count}/{total} passed")

    if not all_outcomes:
        print("No test outcomes recorded across any run.")
        return 1

    flaky: list[str] = []
    always_fail: list[str] = []
    stable_pass: list[str] = []

    for node_id, results in sorted(all_outcomes.items()):
        if len(set(results)) > 1:
            pass_count = sum(results)
            flaky.append(f"  {node_id}  ({pass_count}/{len(results)} runs passed)")
        elif not results[0]:
            always_fail.append(f"  {node_id}")
        else:
            stable_pass.append(node_id)

    print(f"\n{'='*60}")
    print(f"Flaky tests ({len(flaky)}):")
    for f in flaky:
        print(f)

    if always_fail:
        print(f"\nAlways failing ({len(always_fail)}):")
        for f in always_fail:
            print(f)

    print(f"\nStable passing: {len(stable_pass)}/{len(all_outcomes)} tests")
    print(f"{'='*60}")

    return 1 if flaky else 0


if __name__ == "__main__":
    raise SystemExit(main())
