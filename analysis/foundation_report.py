#!/usr/bin/env python3
"""Foundation quality report + first-look validation.

Proves the normalizer and resolver work on the real corpus, and emits the first
concrete cross-source signals:

  out/foundation_report.json        machine-readable summary
  out/actor_provider_matrix.csv     each canonical actor x which providers report it
  out/hard_indicator_overlaps.csv   same hard indicator seen under >1 provider or actor

The overlaps file is a *teaser* of the overlap analysis to come; here it doubles
as a normalization sanity check (if the normalizer works, real shared infra
surfaces; if it's broken, nothing matches).

stdlib only. Run from repo root: python3 analysis/foundation_report.py
(after build_index.py).
"""
import csv
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IDX = os.path.join(OUT, "normalized_indicators.csv")

HARD = {"netloc", "ip", "hash", "handle", "package", "wallet"}


def main():
    with open(IDX, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # ---- coverage ----
    by_class = Counter(r["ind_class"] for r in rows)
    named_rows = sum(1 for r in rows if r["actor_is_named"] == "True")

    # ---- actor x provider matrix ----
    actor = defaultdict(lambda: {"name": "", "country": "", "named": False,
                                 "providers": set(), "rows": 0})
    for r in rows:
        a = actor[r["actor_id"]]
        a["name"] = r["actor_name"]
        a["country"] = r["actor_country"]
        a["named"] = r["actor_is_named"] == "True"
        a["providers"].add(r["source_provider"])
        a["rows"] += 1
    cross_provider = {k: v for k, v in actor.items() if len(v["providers"]) > 1}

    with open(os.path.join(OUT, "actor_provider_matrix.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["actor_id", "actor_name", "is_named", "country",
                    "n_providers", "providers", "n_rows"])
        for k, v in sorted(actor.items(), key=lambda kv: -len(kv[1]["providers"])):
            w.writerow([k, v["name"], v["named"], v["country"],
                        len(v["providers"]), "|".join(sorted(v["providers"])),
                        v["rows"]])

    # ---- hard-indicator overlaps (same key, >1 provider OR >1 named actor) ----
    keymap = defaultdict(lambda: {"providers": set(), "actors": set(), "rows": []})
    for r in rows:
        if r["ind_class"] not in HARD or not r["ind_key"]:
            continue
        g = keymap[(r["ind_class"], r["ind_key"])]
        g["providers"].add(r["source_provider"])
        g["actors"].add(r["actor_id"])
        g["rows"].append(r)
    overlaps = {k: v for k, v in keymap.items()
                if len(v["providers"]) > 1 or len(v["actors"]) > 1}
    with open(os.path.join(OUT, "hard_indicator_overlaps.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ind_class", "ind_key", "n_providers", "providers",
                    "n_actors", "actors", "n_rows"])
        for (cls, key), v in sorted(overlaps.items(),
                                    key=lambda kv: (-len(kv[1]["providers"]),
                                                    -len(kv[1]["actors"]))):
            w.writerow([cls, key, len(v["providers"]), "|".join(sorted(v["providers"])),
                        len(v["actors"]), "|".join(sorted(v["actors"])),
                        len(v["rows"])])

    summary = {
        "rows": len(rows),
        "indicator_classes": dict(by_class.most_common()),
        "rows_with_named_actor": named_rows,
        "canonical_actors": len(actor),
        "named_actors": sum(1 for v in actor.values() if v["named"]),
        "actors_in_multiple_providers": len(cross_provider),
        "hard_overlap_keys": len(overlaps),
        "cross_provider_overlap_keys":
            sum(1 for v in overlaps.values() if len(v["providers"]) > 1),
    }
    with open(os.path.join(OUT, "foundation_report.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    # ---- human-readable ----
    print("=== FOUNDATION REPORT ===")
    print(f"rows: {summary['rows']}   named-actor rows: {named_rows}")
    print(f"canonical actors: {summary['canonical_actors']} "
          f"({summary['named_actors']} named)")
    print(f"indicator classes: {summary['indicator_classes']}")
    print(f"\nactors reported by >1 provider (corroboration seed): "
          f"{len(cross_provider)}")
    for k, v in sorted(cross_provider.items(), key=lambda kv: -len(kv[1]["providers"])):
        if v["named"]:
            print(f"   {v['name']:34} [{'+'.join(sorted(v['providers']))}] "
                  f"{v['rows']} rows  ({v['country']})")
    print(f"\nhard-indicator overlap keys: {summary['hard_overlap_keys']} "
          f"({summary['cross_provider_overlap_keys']} span >1 provider)")
    ex = sorted(overlaps.items(), key=lambda kv: -len(kv[1]["providers"]))[:8]
    for (cls, key), v in ex:
        print(f"   {cls:7} {key[:40]:42} providers={sorted(v['providers'])} "
              f"actors={len(v['actors'])}")


if __name__ == "__main__":
    main()
