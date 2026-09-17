#!/usr/bin/env python3
"""Quick win — activity timeline (first/last seen).

When each actor and each origin country surfaces across the reporting, and over
how long. Good for separating persistent operations from one-offs.

Outputs:
  out/timeline_actor.csv     per canonical actor: first/last report date, span,
                             number of reports, providers
  out/timeline_country.csv   same, per origin country

Run from repo root: python3 analysis/timeline.py
"""
import csv
import os
import sys
from collections import defaultdict
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_index import load_index  # noqa: E402

OUT = os.path.join(HERE, "out")


def _d(s):
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def summarize(rows, keyfn, name_col, path, named_only=False):
    agg = defaultdict(lambda: {"dates": set(), "reports": set(),
                               "providers": set(), "name": "", "country": ""})
    for r in rows:
        if named_only and r["actor_is_named"] != "True":
            continue
        k = keyfn(r)
        if not k:
            continue
        a = agg[k]
        d = _d(r["report_date"])
        if d:
            a["dates"].add(d)
        a["reports"].add(r["source_report"])
        a["providers"].add(r["source_provider"])
        a["name"] = r["actor_name"]
        a["country"] = r["actor_country"]
    os.makedirs(OUT, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([name_col, "country", "first_seen", "last_seen", "span_days",
                    "n_reports", "n_providers", "providers"])
        for k, a in sorted(agg.items(),
                           key=lambda kv: (min(kv[1]["dates"])
                                           if kv[1]["dates"] else date.max)):
            if a["dates"]:
                lo, hi = min(a["dates"]), max(a["dates"])
                span = (hi - lo).days
            else:
                lo = hi = ""; span = ""
            w.writerow([k, a["country"], lo, hi, span, len(a["reports"]),
                        len(a["providers"]), "|".join(sorted(a["providers"]))])
    return agg


def main():
    rows = load_index()
    ta = summarize(rows, lambda r: r["actor_name"], "actor",
                   os.path.join(OUT, "timeline_actor.csv"), named_only=True)
    tc = summarize(rows, lambda r: r["actor_country"], "origin_country",
                   os.path.join(OUT, "timeline_country.csv"))
    print(f"timeline: {len(ta)} named actors, {len(tc)} origin countries")
    print("  -> out/timeline_actor.csv, out/timeline_country.csv")
    persistent = sorted(
        ((k, a) for k, a in ta.items() if len(a["dates"]) > 1),
        key=lambda kv: (max(kv[1]["dates"]) - min(kv[1]["dates"])).days,
        reverse=True)[:5]
    print("  longest-running named actors:")
    for k, a in persistent:
        lo, hi = min(a["dates"]), max(a["dates"])
        print(f"     {a['name']:32} {lo} -> {hi} "
              f"({(hi - lo).days} d, {len(a['providers'])} providers)")


if __name__ == "__main__":
    main()
