#!/usr/bin/env python3
"""#3 — network-level impact metrics.

Pulls quantitative reach metrics from the corpus and aggregates them by actor
and by origin country. Two sources:
  - asset_count rows (already structured: metric_n / metric_unit)
  - numbers embedded in description free-text (followers, ad spend, accounts,
    pages, groups) — these providers rarely put reach in a dedicated field.

Honest note: metric coverage is sparse and uneven (X gives account counts,
Meta some asset counts, others almost none). Treat totals as lower bounds, not
platform-complete figures.

Outputs:
  out/impact_by_actor.csv     per canonical actor, summed by unit
  out/impact_by_country.csv   per origin country, summed by unit
  out/impact_line_items.csv    every metric found, with its source row

Run from repo root: python3 analysis/impact.py
"""
import csv
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_index import load_index  # noqa: E402
from normalize import refang  # noqa: E402

OUT = os.path.join(HERE, "out")

_MULT = {"k": 1_000, "thousand": 1_000, "m": 1_000_000, "million": 1_000_000}
_SPEND = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s?(k|m|million|thousand)?", re.I)
_REACH = re.compile(r"([\d,]+)\+?\s+(followers|subscribers|views|likes|"
                    r"accounts|pages|groups|channels)", re.I)


def extract(desc: str):
    """Yield (unit, value) metrics found in a description string."""
    d = refang(desc or "")
    for m in _SPEND.finditer(d):
        val = float(m.group(1).replace(",", ""))
        val *= _MULT.get((m.group(2) or "").lower(), 1)
        yield ("usd_spend", int(val))
    for m in _REACH.finditer(d):
        yield (m.group(2).lower(), int(m.group(1).replace(",", "")))


def main():
    rows = load_index()
    line_items = []   # (actor_id, actor_name, country, provider, unit, n, source)
    for r in rows:
        aid, an, ac, prov = (r["actor_id"], r["actor_name"], r["actor_country"],
                             r["source_provider"])
        if r["metric_n"]:
            line_items.append((aid, an, ac, prov, r["metric_unit"],
                               int(r["metric_n"]), r["indicator_value"]))
        for unit, n in extract(r["description"]):
            line_items.append((aid, an, ac, prov, unit, n, r["description"][:80]))

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "impact_line_items.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["actor_id", "actor_name", "country", "provider", "unit",
                    "value", "source"])
        for li in line_items:
            w.writerow(li)

    def agg(keyfn):
        d = defaultdict(lambda: defaultdict(int))
        meta = {}
        for aid, an, ac, prov, unit, n, _ in line_items:
            k = keyfn(aid, an, ac)
            d[k][unit] += n
            meta[k] = (an, ac)
        return d, meta

    by_actor, ameta = agg(lambda aid, an, ac: aid)
    units = sorted({u for d in by_actor.values() for u in d})
    with open(os.path.join(OUT, "impact_by_actor.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["actor_id", "actor_name", "country"] + units)
        for k, d in sorted(by_actor.items(),
                           key=lambda kv: -sum(kv[1].values())):
            an, ac = ameta[k]
            w.writerow([k, an, ac] + [d.get(u, "") for u in units])

    by_country = defaultdict(lambda: defaultdict(int))
    for aid, an, ac, prov, unit, n, _ in line_items:
        by_country[ac or "(unknown)"][unit] += n
    with open(os.path.join(OUT, "impact_by_country.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["country"] + units)
        for c, d in sorted(by_country.items(),
                           key=lambda kv: -sum(kv[1].values())):
            w.writerow([c] + [d.get(u, "") for u in units])

    print(f"impact: {len(line_items)} metric line-items; units={units}")
    print("  -> out/impact_by_actor.csv, out/impact_by_country.csv, "
          "out/impact_line_items.csv")
    print("  top countries by account reach:")
    for c, d in sorted(by_country.items(),
                       key=lambda kv: -kv[1].get("accounts", 0))[:6]:
        if d.get("accounts"):
            print(f"     {c:20} {d['accounts']:>8,} accounts")


if __name__ == "__main__":
    main()
