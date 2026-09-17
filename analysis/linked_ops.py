#!/usr/bin/env python3
"""#2 — linked operations graph.

Builds a bipartite graph of canonical actors <-> hard indicators, then finds
clusters of actors tied together by shared infrastructure (and by alias
resolution). A cluster spanning more than one provider is the "same network
seen in two companies' reporting" signal.

Outputs:
  out/linked_ops_edges.csv        actor_id, ind_class, ind_key  (one per link)
  out/linked_ops_bridges.csv      indicators shared by >1 actor (the pivots)
  out/linked_ops_components.csv    connected components (actors joined by shared
                                   infra): providers, actors, bridge indicators
  out/linked_ops.graphml          Gephi/Cytoscape-importable graph

Run from repo root: python3 analysis/linked_ops.py
"""
import csv
import os
import sys
from collections import defaultdict
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_index import load_index  # noqa: E402
from normalize import STOPLIST  # noqa: E402

OUT = os.path.join(HERE, "out")
HARD = {"netloc", "ip", "hash", "handle", "package", "wallet"}

# An indicator shared by this many or more distinct actors is treated as a hub
# (a benign shared platform or common service), not attributable infrastructure,
# and excluded from clustering so it can't over-merge unrelated networks.
DEGREE_CAP = 6


def is_hub(cls, key, n_actors):
    """A bridge is dropped if it's a stoplisted host or shared too widely."""
    if cls == "netloc" and key in STOPLIST:
        return True
    return n_actors >= DEGREE_CAP


class UF:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def main():
    rows = load_index()
    actor_name = {}
    actor_prov = defaultdict(set)
    edges = set()                       # (actor_id, class, key)
    key_actors = defaultdict(set)       # (class,key) -> {actor_id}
    for r in rows:
        actor_name[r["actor_id"]] = r["actor_name"]
        actor_prov[r["actor_id"]].add(r["source_provider"])
        if r["ind_class"] in HARD and r["ind_key"]:
            edges.add((r["actor_id"], r["ind_class"], r["ind_key"]))
            key_actors[(r["ind_class"], r["ind_key"])].add(r["actor_id"])

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "linked_ops_edges.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["actor_id", "ind_class", "ind_key"])
        for e in sorted(edges): w.writerow(e)

    # bridges: indicators tying >1 actor together, minus hubs (stoplisted hosts
    # and indicators shared so widely they're not attributable infrastructure)
    shared = {k: v for k, v in key_actors.items() if len(v) > 1}
    bridges = {k: v for k, v in shared.items() if not is_hub(k[0], k[1], len(v))}
    hubs = {k: v for k, v in shared.items() if is_hub(k[0], k[1], len(v))}
    with open(os.path.join(OUT, "linked_ops_hubs.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ind_class", "ind_key", "n_actors", "reason"])
        for (cls, key), acts in sorted(hubs.items(), key=lambda kv: -len(kv[1])):
            reason = "stoplist" if (cls == "netloc" and key in STOPLIST) \
                else f"degree>={DEGREE_CAP}"
            w.writerow([cls, key, len(acts), reason])
    with open(os.path.join(OUT, "linked_ops_bridges.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ind_class", "ind_key", "n_actors", "actors", "n_providers",
                    "providers"])
        for (cls, key), acts in sorted(bridges.items(), key=lambda kv: -len(kv[1])):
            provs = set().union(*(actor_prov[a] for a in acts))
            w.writerow([cls, key, len(acts),
                        " ; ".join(sorted(actor_name[a] for a in acts)),
                        len(provs), "|".join(sorted(provs))])

    # connected components over actors joined by shared indicators
    uf = UF()
    for a in actor_name:
        uf.find(a)
    for acts in bridges.values():
        acts = list(acts)
        for other in acts[1:]:
            uf.union(acts[0], other)
    comp = defaultdict(set)
    for a in actor_name:
        comp[uf.find(a)].add(a)
    with open(os.path.join(OUT, "linked_ops_components.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["component_id", "n_actors", "actors", "n_providers",
                    "providers", "n_bridge_indicators"])
        cid = 0
        for root, acts in sorted(comp.items(), key=lambda kv: -len(kv[1])):
            if len(acts) < 2:
                continue
            cid += 1
            provs = set().union(*(actor_prov[a] for a in acts))
            nb = sum(1 for (cls, key), ba in bridges.items() if ba & acts)
            w.writerow([f"C{cid}", len(acts),
                        " ; ".join(sorted(actor_name[a] for a in acts)),
                        len(provs), "|".join(sorted(provs)), nb])

    # GraphML for Gephi
    with open(os.path.join(OUT, "linked_ops.graphml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'
                 '<key id="kind" for="node" attr.name="kind" attr.type="string"/>\n'
                 '<key id="label" for="node" attr.name="label" attr.type="string"/>\n'
                 '<graph edgedefault="undirected">\n')
        for a, nm in actor_name.items():
            fh.write(f'<node id="a::{escape(a)}"><data key="kind">actor</data>'
                     f'<data key="label">{escape(nm)}</data></node>\n')
        for (cls, key) in bridges:
            nid = f"i::{cls}::{key}"
            fh.write(f'<node id="{escape(nid)}"><data key="kind">{cls}</data>'
                     f'<data key="label">{escape(key)}</data></node>\n')
        eid = 0
        for (a, cls, key) in edges:
            if (cls, key) in bridges:
                eid += 1
                fh.write(f'<edge id="e{eid}" source="a::{escape(a)}" '
                         f'target="i::{escape(cls)}::{escape(key)}"/>\n')
        fh.write('</graph></graphml>\n')

    multi = [(root, acts) for root, acts in comp.items() if len(acts) > 1]
    xprov = [a for _, a in multi
             if len(set().union(*(actor_prov[x] for x in a))) > 1]
    print(f"linked-ops: {len(bridges)} bridge indicators "
          f"({len(hubs)} hubs excluded), {len(multi)} actor clusters "
          f"({len(xprov)} span >1 provider)")
    print("  -> out/linked_ops_{edges,bridges,components,hubs}.csv, "
          "linked_ops.graphml")
    for root, acts in sorted(multi, key=lambda kv: -len(kv[1]))[:5]:
        provs = set().union(*(actor_prov[a] for a in acts))
        names = sorted(actor_name[a] for a in acts)
        print(f"   [{'+'.join(sorted(provs))}] {len(acts)} actors: "
              f"{'; '.join(names[:3])}{' ...' if len(names) > 3 else ''}")


if __name__ == "__main__":
    main()
