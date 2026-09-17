#!/usr/bin/env python3
"""#1 — cross-dataset indicator overlap.

Finds every indicator that appears in more than one place after normalization,
and tags each overlap with a confidence reflecting how strong that indicator
type is as a link:

  strong   ip, hash, netloc (domain/url/email host), wallet, onion, package
  medium   handle (telegram/social), github
  weak     malware/tool family name, persona, filename (shared by many actors)

Outputs:
  out/overlap_indicators.csv    one row per shared indicator: the value, the
                                distinct providers/actors/reports it links, conf
  out/overlap_by_source_pair.csv how many indicators each provider-pair shares

Run from repo root: python3 analysis/overlap.py
"""
import csv
import os
import sys
from collections import defaultdict
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_index import load_index  # noqa: E402
from normalize import STOPLIST  # noqa: E402

OUT = os.path.join(HERE, "out")
STRONG = {"ip", "hash", "netloc", "wallet", "package"}
MEDIUM = {"handle"}
SKIP = {"text", "metric", "other"}   # not useful as overlap links


def conf(cls):
    return "strong" if cls in STRONG else "medium" if cls in MEDIUM else "weak"


def main():
    rows = load_index()
    groups = defaultdict(lambda: {"providers": set(), "actors": set(),
                                  "reports": set(), "rows": []})
    for r in rows:
        cls = r["ind_class"]
        if cls in SKIP or not r["ind_key"]:
            continue
        if cls == "netloc" and r["ind_key"] in STOPLIST:
            continue  # benign shared platform, not a meaningful overlap
        g = groups[(cls, r["ind_key"])]
        g["providers"].add(r["source_provider"])
        g["actors"].add((r["actor_id"], r["actor_name"]))
        g["reports"].add(r["source_report"])
        g["rows"].append(r)

    # an overlap = same normalized indicator under >1 distinct actor OR provider
    overlaps = {k: v for k, v in groups.items()
                if len(v["actors"]) > 1 or len(v["providers"]) > 1}

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "overlap_indicators.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["confidence", "ind_class", "ind_key", "n_providers",
                    "providers", "n_actors", "actors", "n_reports", "reports"])
        # strong first, then by breadth
        for (cls, key), v in sorted(
                overlaps.items(),
                key=lambda kv: (STRONG.__contains__(kv[0][0]) is False,
                                -len(kv[1]["providers"]), -len(kv[1]["actors"]))):
            w.writerow([conf(cls), cls, key, len(v["providers"]),
                        "|".join(sorted(v["providers"])), len(v["actors"]),
                        " ; ".join(sorted(n for _, n in v["actors"])),
                        len(v["reports"]), " ; ".join(sorted(v["reports"]))])

    # provider-pair summary
    pair = defaultdict(lambda: defaultdict(int))
    for (cls, key), v in overlaps.items():
        if len(v["providers"]) > 1:
            for a, b in combinations(sorted(v["providers"]), 2):
                pair[(a, b)][conf(cls)] += 1
    with open(os.path.join(OUT, "overlap_by_source_pair.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["provider_a", "provider_b", "strong", "medium", "weak", "total"])
        for (a, b), c in sorted(pair.items(), key=lambda kv: -sum(kv[1].values())):
            w.writerow([a, b, c["strong"], c["medium"], c["weak"],
                        sum(c.values())])

    xprov = sum(1 for v in overlaps.values() if len(v["providers"]) > 1)
    strong = sum(1 for (cls, _) in overlaps if cls in STRONG)
    print(f"overlap: {len(overlaps)} shared indicators "
          f"({strong} strong-type, {xprov} span >1 provider)")
    print(f"  -> out/overlap_indicators.csv, out/overlap_by_source_pair.csv")
    for (cls, key), v in list(sorted(
            overlaps.items(), key=lambda kv: -len(kv[1]["providers"])))[:6]:
        if len(v["providers"]) > 1:
            print(f"   [{conf(cls)}] {cls} {key}  <- {sorted(v['providers'])}")


if __name__ == "__main__":
    main()
