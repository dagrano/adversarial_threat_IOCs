#!/usr/bin/env python3
"""Build the normalized index — the enriched table every other analysis reads.

Reads dist/indicators.csv, applies indicator normalization (normalize.py) and
actor resolution (resolve.py), and writes analysis/out/normalized_indicators.csv
with these columns added to the originals:

  ind_class        match class (netloc, ip, hash, handle, package, ...)
  ind_key          normalized value to match on
  ind_host         registrable host (netloc types only)
  actor_id         canonical actor id (or LABEL:... for generic network labels)
  actor_name       canonical actor display name
  actor_country    resolved origin country
  actor_is_named   True for a named actor, False for a per-report label
  metric_n         integer count parsed from asset_count rows (else blank)
  metric_unit      normalized unit (accounts/pages/groups/...) for those rows

stdlib only. Run from the repo root: python3 analysis/build_index.py
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from normalize import canonicalize, parse_metric  # noqa: E402
from resolve import resolve  # noqa: E402

SRC = os.path.join(ROOT, "dist", "indicators.csv")
OUT_DIR = os.path.join(HERE, "out")
OUT = os.path.join(OUT_DIR, "normalized_indicators.csv")

EXTRA = ["ind_class", "ind_key", "ind_host", "actor_id", "actor_name",
         "actor_country", "actor_is_named", "metric_n", "metric_unit"]


def build():
    with open(SRC, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    fields = list(rows[0].keys()) + EXTRA
    actor_cache = {}
    out = []
    for r in rows:
        c = canonicalize(r["indicator_type"], r["indicator_value"])
        a_key = r["actor"]
        if a_key not in actor_cache:
            actor_cache[a_key] = resolve(a_key)
        a = actor_cache[a_key]
        mn, mu = "", ""
        if r["indicator_type"] == "asset_count":
            pm = parse_metric(r["indicator_value"])
            if pm:
                mn, mu = pm
        row = dict(r)
        row.update(ind_class=c["class"], ind_key=c["key"], ind_host=c["host"],
                   actor_id=a["canonical_id"], actor_name=a["canonical_name"],
                   actor_country=a["country"], actor_is_named=a["is_named"],
                   metric_n=mn, metric_unit=mu)
        out.append(row)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    named = sum(1 for r in out if r["actor_is_named"])
    print(f"Wrote {OUT}")
    print(f"  {len(out)} rows | {len({r['actor_id'] for r in out})} canonical actors "
          f"({len({r['actor_id'] for r in out if r['actor_is_named']})} named)")
    print(f"  {named} rows resolved to a named actor; "
          f"{len(out) - named} rows are per-report network labels")
    return out


def load_index(rebuild=False):
    """Return the enriched index rows, building it first if missing/stale."""
    if rebuild or not os.path.exists(OUT):
        build()
    with open(OUT, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    build()
