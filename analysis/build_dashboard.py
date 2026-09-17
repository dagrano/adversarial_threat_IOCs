#!/usr/bin/env python3
"""Render a self-contained HTML dashboard from the analysis CSVs.

Reads the reports under analysis/out/ and writes analysis/out/dashboard.html —
a single file with all data embedded inline (no external requests, opens offline
and on GitHub Pages). Light/dark aware. Run after the analysis scripts:

    python3 analysis/build_index.py
    for s in foundation_report overlap linked_ops impact corroboration timeline; \\
        do python3 analysis/$s.py; done
    python3 analysis/build_dashboard.py
"""
import csv
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def rd(name):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def jload(name):
    p = os.path.join(OUT, name)
    return json.load(open(p)) if os.path.exists(p) else {}


PROVIDERS = ["anthropic", "openai", "meta", "google", "tiktok", "x"]
# categorical slots 1-6 (validated order), providers in fixed order
PCOLOR = {"anthropic": 1, "openai": 2, "meta": 3, "google": 4, "tiktok": 5, "x": 6}


def esc(s):
    return html.escape(str(s))


def main():
    summ = jload("foundation_report.json")
    corro = rd("corroboration_country_provider.csv")
    impact = rd("impact_by_country.csv")
    overl = rd("overlap_indicators.csv")
    comps = rd("linked_ops_components.csv")
    tl = rd("timeline_actor.csv")
    amx = rd("actor_provider_matrix.csv")

    # ---- overview tiles ----
    cross_actor = sum(1 for r in amx if r.get("is_named") == "True"
                      and int(r["n_providers"]) > 1)
    tiles = [
        ("Indicator rows", f"{summ.get('rows', 0):,}"),
        ("Sources", "6"),
        ("Named actors", str(summ.get("named_actors", 0))),
        ("Origin countries", str(len(corro))),
        ("Cross-provider actors", str(cross_actor)),
        ("Cross-provider overlaps", str(summ.get("cross_provider_overlap_keys", 0))),
    ]

    # ---- corroboration heatmap (country x provider, sequential blue) ----
    cmax = max((int(r["total_rows"]) for r in corro), default=1)
    import math
    def seq(v):
        if v <= 0:
            return "var(--surface-2)"
        t = math.log1p(v) / math.log1p(cmax)      # log scale, wide dynamic range
        steps = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
        return steps[min(len(steps) - 1, int(t * len(steps)))]
    def ink(v):
        return "#fff" if v > 0 and math.log1p(v) / math.log1p(cmax) > 0.55 else "var(--text-primary)"

    heat = ['<table class="heat"><thead><tr><th>Origin country</th>']
    for p in PROVIDERS:
        heat.append(f'<th class="pv">{esc(p)}</th>')
    heat.append("<th>providers</th></tr></thead><tbody>")
    for r in corro[:20]:
        heat.append(f'<tr><td class="rl">{esc(r["origin_country"] or "(unknown)")}</td>')
        for p in PROVIDERS:
            v = int(r.get(p) or 0)
            cell = f"{v:,}" if v else ""
            heat.append(f'<td class="cell" style="background:{seq(v)};color:{ink(v)}" '
                        f'title="{esc(r["origin_country"])} · {p}: {v} rows">{cell}</td>')
        heat.append(f'<td class="np">{esc(r["n_providers"])}</td></tr>')
    heat.append("</tbody></table>")

    # ---- impact bars (accounts by country, single hue) ----
    imp = [(r["country"] or "(unknown)", int(r.get("accounts") or 0)) for r in impact]
    imp = [x for x in imp if x[1] > 0][:12]
    imax = max((v for _, v in imp), default=1)
    bars = ['<div class="bars">']
    for name, v in imp:
        w = max(2, round(100 * v / imax))
        bars.append(
            f'<div class="brow"><span class="blabel">{esc(name)}</span>'
            f'<span class="btrack"><span class="bfill" style="width:{w}%" '
            f'title="{esc(name)}: {v:,} accounts"></span></span>'
            f'<span class="bval">{v:,}</span></div>')
    bars.append("</div>")

    # ---- overlaps table (strong first, cross-provider flagged) ----
    def xprov(r):
        return int(r["n_providers"]) > 1
    ov_sorted = sorted(overl, key=lambda r: (not xprov(r),
                                             r["confidence"] != "strong",
                                             -int(r["n_actors"])))[:15]
    ovr = ['<table class="tbl"><thead><tr><th>conf</th><th>type</th><th>indicator</th>'
           '<th>providers</th><th>actors</th></tr></thead><tbody>']
    for r in ov_sorted:
        badge = "xp" if xprov(r) else ""
        ovr.append(
            f'<tr><td><span class="pill {esc(r["confidence"])}">{esc(r["confidence"])}</span></td>'
            f'<td class="mono">{esc(r["ind_class"])}</td>'
            f'<td class="mono {badge}">{esc(r["ind_key"])}</td>'
            f'<td>{esc(r["providers"].replace("|", ", "))}</td>'
            f'<td>{esc(r["n_actors"])}</td></tr>')
    ovr.append("</tbody></table>")

    # ---- linked-ops components ----
    cmp_cards = ['<div class="cards">']
    for r in comps:
        prov = r["providers"].replace("|", " + ")
        multi = "multi" if int(r["n_providers"]) > 1 else ""
        cmp_cards.append(
            f'<div class="card {multi}"><div class="ct">{esc(r["component_id"])} · '
            f'{esc(r["n_actors"])} actors · <span class="cp">{esc(prov)}</span></div>'
            f'<div class="cb">{esc(r["actors"].replace(" ; ", " · "))}</div>'
            f'<div class="cf">{esc(r["n_bridge_indicators"])} shared indicators</div></div>')
    cmp_cards.append("</div>")

    # ---- timeline (named actor spans) ----
    dated = [r for r in tl if r["first_seen"] and r["last_seen"]]
    if dated:
        lo = min(r["first_seen"] for r in dated)
        hi = max(r["last_seen"] for r in dated)
        from datetime import date
        d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
        span = max(1, (d1 - d0).days)
        trows = ['<div class="tl">']
        for r in sorted(dated, key=lambda x: x["first_seen"]):
            a, b = date.fromisoformat(r["first_seen"]), date.fromisoformat(r["last_seen"])
            left = 100 * (a - d0).days / span
            width = max(1.2, 100 * (b - a).days / span)
            xp = "multi" if int(r["n_providers"]) > 1 else ""
            trows.append(
                f'<div class="tlrow"><span class="tlname">{esc(r["actor"])}</span>'
                f'<span class="tltrack"><span class="tlbar {xp}" style="left:{left:.1f}%;'
                f'width:{width:.1f}%" title="{esc(r["actor"])}: {r["first_seen"]} → '
                f'{r["last_seen"]} ({r["n_providers"]} providers)"></span></span></div>')
        trows.append(f'<div class="tlaxis"><span>{lo}</span><span>{hi}</span></div></div>')
    else:
        trows = ["<p>No dated actors.</p>"]

    legend = " ".join(
        f'<span class="lg"><i style="background:var(--series-{PCOLOR[p]})"></i>{p}</span>'
        for p in PROVIDERS)

    doc = TEMPLATE.format(
        tiles="".join(f'<div class="tile"><div class="tv">{esc(v)}</div>'
                      f'<div class="tk">{esc(k)}</div></div>' for k, v in tiles),
        legend=legend, heat="".join(heat), bars="".join(bars), overl="".join(ovr),
        comps="".join(cmp_cards), timeline="".join(trows))
    with open(os.path.join(OUT, "dashboard.html"), "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"Wrote {os.path.join(OUT, 'dashboard.html')}")


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Adversarial Threat IOCs — analysis</title>
<style>
:root{{
  color-scheme: light dark;
  --plane:#f9f9f7; --surface-1:#fcfcfb; --surface-2:#eef0f2;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --muted:#898781;
  --grid:#e1e0d9; --border:rgba(11,11,11,.10);
  --series-1:#2a78d6; --series-2:#eb6834; --series-3:#1baf7a;
  --series-4:#eda100; --series-5:#e87ba4; --series-6:#008300;
  --good:#0ca30c; --warn:#eda100; --crit:#d03b3b;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12);
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70;
  --series-4:#c98500; --series-5:#d55181; --series-6:#008300;
}}}}
:root[data-theme=dark]{{
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12);
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70;
  --series-4:#c98500; --series-5:#d55181; --series-6:#008300;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--plane);color:var(--text-primary);
  font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:24px}}
.wrap{{max-width:1080px;margin:0 auto}}
h1{{font-size:22px;margin:0 0 2px}} .sub{{color:var(--text-secondary);margin:0 0 20px}}
h2{{font-size:15px;margin:28px 0 10px;letter-spacing:.01em}}
.note{{color:var(--muted);font-size:12px;margin:-6px 0 12px}}
section{{background:var(--surface-1);border:1px solid var(--border);
  border-radius:12px;padding:16px 18px;margin-bottom:14px}}
.tiles{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}}
@media(max-width:720px){{.tiles{{grid-template-columns:repeat(2,1fr)}}}}
.tile{{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:12px}}
.tv{{font-size:24px;font-weight:650}} .tk{{color:var(--text-secondary);font-size:12px;margin-top:2px}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin:2px 0 6px;color:var(--text-secondary);font-size:12px}}
.lg{{display:inline-flex;align-items:center;gap:5px}}
.lg i{{width:10px;height:10px;border-radius:2px;display:inline-block}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}}
.heat td,.heat th{{text-align:center;padding:5px 6px;border:1px solid var(--surface-1)}}
.heat .rl{{text-align:left;white-space:nowrap;color:var(--text-primary)}}
.heat .pv{{color:var(--text-secondary);font-weight:600}}
.heat .cell{{font-variant-numeric:tabular-nums;min-width:52px}}
.heat .np{{color:var(--muted)}}
.overflow{{overflow-x:auto}}
.bars{{display:flex;flex-direction:column;gap:7px}}
.brow{{display:grid;grid-template-columns:160px 1fr 78px;align-items:center;gap:10px}}
.blabel{{color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.btrack{{background:var(--surface-2);border-radius:4px;height:16px;overflow:hidden}}
.bfill{{display:block;height:100%;background:var(--series-1);border-radius:0 4px 4px 0}}
.bval{{text-align:right;font-variant-numeric:tabular-nums;color:var(--text-primary)}}
.tbl th{{text-align:left;color:var(--text-secondary);font-weight:600;
  border-bottom:1px solid var(--grid);padding:6px 8px}}
.tbl td{{padding:6px 8px;border-bottom:1px solid var(--grid)}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}}
.xp{{font-weight:700}} .xp::after{{content:" ⇄";color:var(--series-2)}}
.pill{{font-size:11px;padding:1px 7px;border-radius:9px;border:1px solid var(--border)}}
.pill.strong{{background:color-mix(in srgb,var(--good) 18%,transparent);color:var(--good)}}
.pill.medium{{background:color-mix(in srgb,var(--warn) 20%,transparent)}}
.pill.weak{{color:var(--muted)}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
@media(max-width:720px){{.cards{{grid-template-columns:1fr}}}}
.card{{border:1px solid var(--border);border-radius:10px;padding:10px 12px;background:var(--surface-1)}}
.card.multi{{border-color:var(--series-2)}}
.ct{{font-weight:600;font-size:12.5px;margin-bottom:4px}} .cp{{color:var(--series-2)}}
.cb{{color:var(--text-secondary);font-size:12px}} .cf{{color:var(--muted);font-size:11.5px;margin-top:5px}}
.tl{{display:flex;flex-direction:column;gap:6px}}
.tlrow{{display:grid;grid-template-columns:200px 1fr;align-items:center;gap:10px}}
.tlname{{color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tltrack{{position:relative;height:14px;background:var(--surface-2);border-radius:4px}}
.tlbar{{position:absolute;height:100%;background:var(--series-1);border-radius:4px;min-width:4px}}
.tlbar.multi{{background:var(--series-2)}}
.tlaxis{{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;
  margin-top:4px;padding-left:210px}}
.foot{{color:var(--muted);font-size:11.5px;margin-top:18px}}
button.tog{{float:right;background:var(--surface-1);color:var(--text-secondary);
  border:1px solid var(--border);border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px}}
</style></head>
<body><div class="wrap">
<button class="tog" onclick="var r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'">◐ theme</button>
<h1>Adversarial Threat IOCs</h1>
<p class="sub">Cross-source analysis of published adversarial-threat reporting — generated from the corpus.</p>
<div class="tiles">{tiles}</div>

<h2>Origin country × provider — corroboration</h2>
<section><div class="legend">{legend}</div>
<div class="note">Row counts, log-shaded. A country covered by several providers is more strongly corroborated.</div>
<div class="overflow">{heat}</div></section>

<h2>Reported account reach by origin country</h2>
<section><div class="note">From asset counts + numbers parsed out of descriptions. Sparse and uneven — lower bounds, not platform-complete.</div>{bars}</section>

<h2>Shared indicators across actors / providers</h2>
<section><div class="note">⇄ marks an indicator seen under more than one provider. Strong = hard IOC (domain/IP/hash).</div>
<div class="overflow">{overl}</div></section>

<h2>Linked-operation clusters</h2>
<section><div class="note">Actors joined by shared infrastructure (benign platform hubs excluded). Orange = spans more than one provider.</div>{comps}</section>

<h2>Named-actor activity timeline</h2>
<section><div class="note">First → last seen across all reporting. Orange = reported by more than one provider.</div>{timeline}</section>

<p class="foot">Generated by analysis/build_dashboard.py. PDF-extracted indicators should be verified against source_url before operational use.</p>
</div></body></html>"""


if __name__ == "__main__":
    main()
