#!/usr/bin/env python3
"""Concatenate every data/**/*.csv into a single master indicators.csv.

Run from the repo root:
    python scripts/build_master.py
Outputs dist/indicators.csv (canonical, sorted) and prints summary stats.
"""
import csv
import glob
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from common import FIELDS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dist", "indicators.csv")


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "**", "*.csv"),
                             recursive=True))
    rows = []
    for f in files:
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rows.append({k: r.get(k, "") for k in FIELDS})
    # stable sort: provider, report_date, actor
    rows.sort(key=lambda r: (r["source_provider"], r["report_date"], r["actor"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    prov = Counter(r["source_provider"] for r in rows)
    itype = Counter(r["indicator_type"] for r in rows)
    print(f"Built {OUT}")
    print(f"  {len(rows)} rows from {len(files)} source files")
    print(f"  by provider: {dict(prov)}")
    print(f"  top indicator types: {dict(itype.most_common(8))}")


if __name__ == "__main__":
    main()
