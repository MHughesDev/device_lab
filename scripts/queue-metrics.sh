#!/usr/bin/env bash
# scripts/queue-metrics.sh
# Summarize queue/audit.log into metrics: median time-to-merge, PR count, complexity distribution.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 <<'PY'
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

audit_log = Path("queue/audit.log")

if not audit_log.is_file():
    print("No queue/audit.log found. Run 'make queue:archive' to generate metrics.")
    sys.exit(0)

records = []
with audit_log.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

if not records:
    print("No metrics records found in audit.log")
    sys.exit(0)

# Calculate metrics
total_pr_count = len([r for r in records if r.get("pr_url")])

# Time-to-merge (from branch_created_at to archived_at)
ttm_days = []
for r in records:
    created = r.get("branch_created_at")
    archived = r.get("archived_at")
    if created and archived:
        try:
            # Parse ISO format dates
            if "T" in created:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            else:
                created_dt = datetime.fromisoformat(created)
            
            if "T" in archived:
                archived_dt = datetime.fromisoformat(archived.replace("Z", "+00:00"))
            else:
                archived_dt = datetime.fromisoformat(archived)
            
            delta = archived_dt - created_dt
            ttm_days.append(delta.total_seconds() / 86400)
        except Exception:
            pass

median_ttm = statistics.median(ttm_days) if ttm_days else None

# Complexity distribution
complexity_counts: dict[str, int] = {}
for r in records:
    c = r.get("complexity", "unknown")
    complexity_counts[c] = complexity_counts.get(c, 0) + 1

# Review rounds distribution
review_rounds_list = [r.get("review_rounds") for r in records if r.get("review_rounds") is not None]
median_review_rounds = statistics.median(review_rounds_list) if review_rounds_list else None

# Print summary
print("=== Queue Metrics Summary ===")
print(f"Total archived items: {len(records)}")
print(f"Items with PR URLs: {total_pr_count}")
print("")

if median_ttm is not None:
    print(f"Median time-to-merge: {median_ttm:.1f} days")
else:
    print("Median time-to-merge: N/A (insufficient data)")

if median_review_rounds is not None:
    print(f"Median review rounds: {median_review_rounds:.1f}")
else:
    print("Median review rounds: N/A (insufficient data)")

print("")
print("Complexity distribution:")
for c in ["S", "M", "L", "XL", "unknown"]:
    count = complexity_counts.get(c, 0)
    pct = (count / len(records) * 100) if records else 0
    print(f"  {c}: {count} ({pct:.1f}%)")

print("")
print("Recent activity (last 10 items):")
for r in reversed(records[-10:]):
    qid = r.get("queue_id", "unknown")
    comp = r.get("complexity", "?")
    status = r.get("status", "?")
    pr = "with PR" if r.get("pr_url") else "no PR"
    print(f"  {qid}: {comp} | {status} | {pr}")
PY
