#!/usr/bin/env python3
"""Quick win — corroboration coverage matrices.

Who is reported by whom. A country or actor covered by several providers is
strongly corroborated; a single-source one is worth scrutiny.

Outputs:
  out/corroboration_actor_provider.csv    named actors x provider (row counts)
  out/corroboration_country_provider.csv   origin country x provider (row counts)

Run from repo root: python3 analysis/corroboration.py
"""
import csv
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_index import load_index  # noqa: E402

OUT = os.path.join(HERE, "out")


def matrix(rows, keyfn, name_col, path, named_only=False):
    provs = sorted({r["source_provider"] for r in rows})
    grid = defaultdict(lambda: defaultdict(int))
    label = {}
    for r in rows:
        if named_only and r["actor_is_named"] != "True":
            continue
        k = keyfn(r)
        if not k:
            continue
        grid[k][r["source_provider"]] += 1
        label[k] = r
    os.makedirs(OUT, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([name_col, "n_providers", "total_rows"] + provs)
        for k, d in sorted(grid.items(),
                           key=lambda kv: (-len({p for p in kv[1]}),
                                           -sum(kv[1].values()))):
            w.writerow([k, len([p for p in d if d[p]]), sum(d.values())]
                       + [d.get(p, "") for p in provs])
    return grid, provs


def main():
    rows = load_index()
    ag, _ = matrix(rows, lambda r: r["actor_name"], "actor",
                   os.path.join(OUT, "corroboration_actor_provider.csv"),
                   named_only=True)
    cg, provs = matrix(rows, lambda r: r["actor_country"], "origin_country",
                       os.path.join(OUT, "corroboration_country_provider.csv"))
    multi_actor = sum(1 for d in ag.values() if len([p for p in d if d[p]]) > 1)
    multi_country = sum(1 for d in cg.values() if len([p for p in d if d[p]]) > 1)
    print(f"corroboration: {len(ag)} named actors "
          f"({multi_actor} multi-provider), {len(cg)} origin countries "
          f"({multi_country} multi-provider)")
    print("  -> out/corroboration_actor_provider.csv, "
          "out/corroboration_country_provider.csv")
    print("  countries by provider breadth:")
    for c, d in sorted(cg.items(),
                       key=lambda kv: -len([p for p in kv[1] if kv[1][p]]))[:6]:
        if c:
            print(f"     {c:20} {len([p for p in d if d[p]])} providers "
                  f"[{'+'.join(sorted(p for p in d if d[p]))}]")


if __name__ == "__main__":
    main()
