#!/usr/bin/env python3
"""Render a self-contained, interactive HTML dashboard from the analysis CSVs.

Reads the reports under analysis/out/ and writes analysis/out/dashboard.html —
a single file with all data embedded inline (no external requests, opens offline
and on GitHub Pages). Light/dark aware.

Interactive layer (vanilla JS, no libraries):
  - provider filter chips (toggle each company's reporting on/off)
  - origin-country map of takedowns (proportional symbols on a graticule)
  - a per-takedown timeline (one marker per disclosed operation, by provider)
All three recompute live from the embedded data when you toggle a company.

A "takedown / operation" = a distinct (provider, source_report, actor) tuple.

Run after the analysis scripts:
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

PROVIDERS = ["anthropic", "openai", "meta", "google", "tiktok", "x"]
PCOLOR = {"anthropic": 1, "openai": 2, "meta": 3, "google": 4, "tiktok": 5, "x": 6}

# Approx country centroids [lon, lat] for proportional-symbol placement.
CENTROIDS = {
    "China": [104, 35], "Russia": [96, 62], "Iran": [53, 32],
    "North Korea": [127, 40], "Pakistan": [70, 30], "Vietnam": [106, 16],
    "France": [2, 47], "Turkey": [35, 39], "Moldova": [29, 47],
    "United Kingdom": [-2, 54], "United States": [-98, 39], "Cambodia": [105, 12],
    "Spain": [-4, 40], "Venezuela": [-66, 7], "United Arab Emirates": [54, 24],
    "Saudi Arabia": [45, 24], "Palestine": [35, 32], "Georgia": [43, 42],
    "India": [79, 22], "Togo": [1, 8], "Myanmar": [96, 21], "Ukraine": [31, 49],
    "Bangladesh": [90, 24], "Croatia": [16, 45], "Israel": [35, 31],
    "Lebanon": [36, 34], "Benin": [2, 9], "Ghana": [-1, 8], "Romania": [25, 46],
    "Belarus": [28, 53], "Poland": [19, 52], "Philippines": [122, 13],
    "Indonesia": [118, -2], "Ecuador": [-78, -1], "Cuba": [-78, 22],
    "Thailand": [101, 15], "Tanzania": [35, -6], "Mexico": [-102, 23],
    "Syria": [38, 35], "Uganda": [32, 1], "Egypt": [30, 26], "Serbia": [21, 44],
    "Nigeria": [8, 9], "Angola": [18, -12], "Honduras": [-86, 15],
    "Bahrain": [50, 26], "Qatar": [51, 25], "Kazakhstan": [67, 48],
    "Germany": [10, 51], "Brazil": [-52, -10], "Malaysia": [112, 3],
    "South Korea": [128, 36], "Japan": [138, 36], "Taiwan": [121, 24],
    "Central African Republic": [21, 7],
}


def rd(name):
    p = os.path.join(OUT, name)
    return list(csv.DictReader(open(p, newline="", encoding="utf-8"))) if os.path.exists(p) else []


def jload(name):
    p = os.path.join(OUT, name)
    return json.load(open(p)) if os.path.exists(p) else {}


def load_world():
    """Natural Earth 110m land geometry (public domain), pre-simplified."""
    p = os.path.join(HERE, "data", "world.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else \
        {"countries": [], "centroids": {}}


def esc(s):
    return html.escape(str(s))


def clean_country(c):
    if not c:
        return "(unknown)"
    # multi-country or actor-name artifacts -> first real token / unknown
    first = c.replace("/", ",").split(",")[0].strip()
    return first if first in CENTROIDS else (first if first != c else c)


def main():
    summ = jload("foundation_report.json")
    corro = rd("corroboration_country_provider.csv")
    impact = rd("impact_by_country.csv")
    overl = rd("overlap_indicators.csv")
    comps = rd("linked_ops_components.csv")
    amx = rd("actor_provider_matrix.csv")
    idx = rd("normalized_indicators.csv")

    # ---- build takedown/operation events: (provider, report, actor_id) ----
    ev = {}
    for r in idx:
        k = (r["source_provider"], r["source_report"], r["actor_id"])
        e = ev.setdefault(k, {"p": r["source_provider"], "c": "", "a": r["actor_name"],
                              "d": r["report_date"], "named": r["actor_is_named"] == "True"})
        if not e["c"] and r["actor_country"]:
            e["c"] = r["actor_country"]
        if r["report_date"] and (not e["d"] or r["report_date"] < e["d"]):
            e["d"] = r["report_date"]
    events = []
    for e in ev.values():
        events.append({"p": e["p"], "c": clean_country(e["c"]), "a": e["a"],
                       "d": e["d"], "named": e["named"]})

    # ---- overview tiles ----
    cross_actor = sum(1 for r in amx if r.get("is_named") == "True"
                      and int(r["n_providers"]) > 1)
    tiles = [
        ("Indicator rows", f"{summ.get('rows', 0):,}"),
        ("Takedowns mapped", str(len(events))),
        ("Named actors", str(summ.get("named_actors", 0))),
        ("Origin countries", str(len(corro))),
        ("Cross-provider actors", str(cross_actor)),
        ("Cross-provider overlaps", str(summ.get("cross_provider_overlap_keys", 0))),
    ]

    # ---- static sections (corroboration heatmap, impact, overlaps, clusters) ----
    import math
    cmax = max((int(r["total_rows"]) for r in corro), default=1)

    def seq(v):
        if v <= 0:
            return "var(--surface-2)"
        t = math.log1p(v) / math.log1p(cmax)
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
            heat.append(f'<td class="cell" style="background:{seq(v)};color:{ink(v)}" '
                        f'title="{esc(r["origin_country"])} · {p}: {v} rows">{v or ""}</td>')
        heat.append(f'<td class="np">{esc(r["n_providers"])}</td></tr>')
    heat.append("</tbody></table>")

    imp = [(r["country"] or "(unknown)", int(r.get("accounts") or 0)) for r in impact]
    imp = [x for x in imp if x[1] > 0][:12]
    imax = max((v for _, v in imp), default=1)
    bars = ['<div class="bars">']
    for name, v in imp:
        w = max(2, round(100 * v / imax))
        bars.append(f'<div class="brow"><span class="blabel">{esc(name)}</span>'
                    f'<span class="btrack"><span class="bfill" style="width:{w}%" '
                    f'title="{esc(name)}: {v:,} accounts"></span></span>'
                    f'<span class="bval">{v:,}</span></div>')
    bars.append("</div>")

    ov_sorted = sorted(overl, key=lambda r: (int(r["n_providers"]) < 2,
                                             r["confidence"] != "strong",
                                             -int(r["n_actors"])))[:15]
    ovr = ['<table class="tbl"><thead><tr><th>conf</th><th>type</th><th>indicator</th>'
           '<th>providers</th><th>actors</th></tr></thead><tbody>']
    for r in ov_sorted:
        badge = "xp" if int(r["n_providers"]) > 1 else ""
        ovr.append(f'<tr><td><span class="pill {esc(r["confidence"])}">{esc(r["confidence"])}</span></td>'
                   f'<td class="mono">{esc(r["ind_class"])}</td>'
                   f'<td class="mono {badge}">{esc(r["ind_key"])}</td>'
                   f'<td>{esc(r["providers"].replace("|", ", "))}</td>'
                   f'<td>{esc(r["n_actors"])}</td></tr>')
    ovr.append("</tbody></table>")

    cmp_cards = ['<div class="cards">']
    for r in comps:
        prov = r["providers"].replace("|", " + ")
        multi = "multi" if int(r["n_providers"]) > 1 else ""
        cmp_cards.append(f'<div class="card {multi}"><div class="ct">{esc(r["component_id"])} · '
                         f'{esc(r["n_actors"])} actors · <span class="cp">{esc(prov)}</span></div>'
                         f'<div class="cb">{esc(r["actors"].replace(" ; ", " · "))}</div>'
                         f'<div class="cf">{esc(r["n_bridge_indicators"])} shared indicators</div></div>')
    cmp_cards.append("</div>")

    chips = "".join(
        f'<button class="chip on" data-p="{p}"><i style="background:var(--series-{PCOLOR[p]})"></i>'
        f'{p}</button>' for p in PROVIDERS)

    doc = TEMPLATE.format(
        tiles="".join(f'<div class="tile"><div class="tv">{esc(v)}</div>'
                      f'<div class="tk">{esc(k)}</div></div>' for k, v in tiles),
        chips=chips, heat="".join(heat), bars="".join(bars), overl="".join(ovr),
        comps="".join(cmp_cards),
        data_json=json.dumps(events, separators=(",", ":")),
        centroids_json=json.dumps(CENTROIDS, separators=(",", ":")),
        world_json=json.dumps(load_world(), separators=(",", ":")),
        pcolor_json=json.dumps(PCOLOR, separators=(",", ":")),
        providers_json=json.dumps(PROVIDERS))
    with open(os.path.join(OUT, "dashboard.html"), "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"Wrote {os.path.join(OUT, 'dashboard.html')} ({len(events)} takedown events)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Adversarial Threat IOCs — analysis</title>
<style>
:root{{
  color-scheme:light dark;
  --plane:#f9f9f7; --surface-1:#fcfcfb; --surface-2:#eef0f2; --ocean:#eaf1f9;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --muted:#898781;
  --grid:#e1e0d9; --border:rgba(11,11,11,.10); --land:#e7e6e0;
  --series-1:#2a78d6; --series-2:#eb6834; --series-3:#1baf7a;
  --series-4:#eda100; --series-5:#e87ba4; --series-6:#008300;
  --good:#0ca30c; --warn:#eda100;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a; --ocean:#12212f;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12); --land:#242423;
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70;
  --series-4:#c98500; --series-5:#d55181; --series-6:#008300;
}}}}
:root[data-theme=dark]{{
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a; --ocean:#12212f;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12); --land:#242423;
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70;
  --series-4:#c98500; --series-5:#d55181; --series-6:#008300;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--plane);color:var(--text-primary);
  font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:24px}}
.wrap{{max-width:1080px;margin:0 auto}}
h1{{font-size:22px;margin:0 0 2px}} .sub{{color:var(--text-secondary);margin:0 0 18px}}
h2{{font-size:15px;margin:26px 0 10px}} .note{{color:var(--muted);font-size:12px;margin:-6px 0 12px}}
section{{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:14px}}
.tiles{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}}
@media(max-width:720px){{.tiles{{grid-template-columns:repeat(2,1fr)}}}}
.tile{{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:12px}}
.tv{{font-size:24px;font-weight:650}} .tk{{color:var(--text-secondary);font-size:12px;margin-top:2px}}
.filterbar{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0 4px}}
.chip{{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);
  background:var(--surface-1);color:var(--text-secondary);border-radius:999px;
  padding:5px 12px;font-size:12.5px;cursor:pointer;user-select:none}}
.chip i{{width:10px;height:10px;border-radius:3px;display:inline-block;opacity:.35}}
.chip.on{{color:var(--text-primary);border-color:var(--text-secondary)}}
.chip.on i{{opacity:1}}
.chip:hover{{border-color:var(--text-secondary)}}
.filtbtn{{background:none;border:none;color:var(--series-1);cursor:pointer;font-size:12px}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin:2px 0 6px;color:var(--text-secondary);font-size:12px}}
.lg{{display:inline-flex;align-items:center;gap:5px}} .lg i{{width:10px;height:10px;border-radius:2px;display:inline-block}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}}
.heat td,.heat th{{text-align:center;padding:5px 6px;border:1px solid var(--surface-1)}}
.heat .rl{{text-align:left;white-space:nowrap}} .heat .pv{{color:var(--text-secondary);font-weight:600}}
.heat .cell{{font-variant-numeric:tabular-nums;min-width:48px}} .heat .np{{color:var(--muted)}}
.overflow{{overflow-x:auto}}
.bars{{display:flex;flex-direction:column;gap:7px}}
.brow{{display:grid;grid-template-columns:160px 1fr 78px;align-items:center;gap:10px}}
.blabel{{color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.btrack{{background:var(--surface-2);border-radius:4px;height:16px;overflow:hidden}}
.bfill{{display:block;height:100%;background:var(--series-1);border-radius:0 4px 4px 0}}
.bval{{text-align:right;font-variant-numeric:tabular-nums}}
.tbl th{{text-align:left;color:var(--text-secondary);font-weight:600;border-bottom:1px solid var(--grid);padding:6px 8px}}
.tbl td{{padding:6px 8px;border-bottom:1px solid var(--grid)}}
.mono{{font-family:ui-monospace,Menlo,monospace;font-size:12px}}
.xp{{font-weight:700}} .xp::after{{content:" ⇄";color:var(--series-2)}}
.pill{{font-size:11px;padding:1px 7px;border-radius:9px;border:1px solid var(--border)}}
.pill.strong{{background:color-mix(in srgb,var(--good) 18%,transparent);color:var(--good)}}
.pill.medium{{background:color-mix(in srgb,var(--warn) 20%,transparent)}}
.pill.weak{{color:var(--muted)}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
@media(max-width:720px){{.cards{{grid-template-columns:1fr}}}}
.card{{border:1px solid var(--border);border-radius:10px;padding:10px 12px}}
.card.multi{{border-color:var(--series-2)}}
.ct{{font-weight:600;font-size:12.5px;margin-bottom:4px}} .cp{{color:var(--series-2)}}
.cb{{color:var(--text-secondary);font-size:12px}} .cf{{color:var(--muted);font-size:11.5px;margin-top:5px}}
#map{{width:100%;height:auto;display:block;background:var(--ocean);border-radius:8px}}
.land{{fill:var(--land);stroke:var(--muted);stroke-width:.4;stroke-opacity:.5}}
.grat{{stroke:var(--grid);stroke-width:.5;fill:none;opacity:.35}}
.bub{{fill:var(--series-1);fill-opacity:.55;stroke:var(--series-1);stroke-width:1.2;cursor:pointer}}
.bub:hover{{fill-opacity:.8}}
.blab{{fill:var(--text-primary);font-size:9px;text-anchor:middle;pointer-events:none}}
.tl{{position:relative}}
.tllane{{display:grid;grid-template-columns:76px 1fr;align-items:center;gap:8px;height:26px}}
.tlp{{color:var(--text-secondary);font-size:12px;text-align:right}}
.tltrack{{position:relative;height:100%;border-bottom:1px solid var(--grid)}}
.tlmark{{position:absolute;top:4px;bottom:4px;width:2px;transform:translateX(-50%);border-radius:1px;cursor:pointer;opacity:.85}}
.tlmark:hover{{opacity:1;width:3px}}
.reglab{{fill:var(--muted);font-size:10px;opacity:.4;text-anchor:middle;pointer-events:none;letter-spacing:.08em}}
.tlaxis{{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;margin:4px 0 0 84px}}
#tip{{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);
  border:1px solid var(--border);border-radius:8px;padding:6px 9px;font-size:12px;opacity:0;
  transition:opacity .08s;z-index:9;max-width:260px;box-shadow:0 4px 14px rgba(0,0,0,.15)}}
.foot{{color:var(--muted);font-size:11.5px;margin-top:18px}}
button.tog{{float:right;background:var(--surface-1);color:var(--text-secondary);border:1px solid var(--border);
  border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px}}
</style></head>
<body><div class="wrap">
<button class="tog" onclick="var r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'">◐ theme</button>
<h1>Adversarial Threat IOCs</h1>
<p class="sub">Cross-source analysis of published adversarial-threat reporting — generated from the corpus.</p>
<div class="tiles">{tiles}</div>

<h2>Filter by reporting company</h2>
<section>
  <div class="filterbar">{chips}
    <button class="filtbtn" id="all">all</button><button class="filtbtn" id="none">none</button>
  </div>
  <div class="note">Toggles apply to the map and the takedown timeline below.</div>
</section>

<h2>Takedowns by origin country</h2>
<section><div class="note">One bubble per origin country, sized by the number of disclosed operations. Hover for the breakdown.</div>
<svg id="map" viewBox="0 0 720 340" role="img" aria-label="World map of takedowns by origin country"></svg>
<div class="legend" id="maplegend"></div></section>

<h2>Origin country × provider — corroboration</h2>
<section><div class="note">Row counts, log-shaded. Static (all providers).</div><div class="overflow">{heat}</div></section>

<h2>Reported account reach by origin country</h2>
<section><div class="note">From asset counts + numbers parsed from descriptions. Lower bounds, not platform-complete.</div>{bars}</section>

<h2>Shared indicators across actors / providers</h2>
<section><div class="note">⇄ marks an indicator seen under more than one provider. Strong = hard IOC.</div><div class="overflow">{overl}</div></section>

<h2>Linked-operation clusters</h2>
<section><div class="note">Actors joined by shared infrastructure (benign hubs excluded). Orange spans more than one provider.</div>{comps}</section>

<h2>Takedown timeline</h2>
<section><div class="note">One marker per disclosed operation, on its report date, in its company's lane. Filtered by the chips above.</div>
<div class="tl" id="timeline"></div><div class="tlaxis" id="tlaxis"></div></section>

<p class="foot">Generated by analysis/build_dashboard.py. PDF-extracted indicators should be verified against source_url before operational use.</p>
</div>
<div id="tip"></div>
<script>
const DATA={data_json};
const CENTROIDS={centroids_json};
const WORLD={world_json};
const ALIAS={{"United States":"United States of America"}};
const PCOLOR={pcolor_json};
const PROVIDERS={providers_json};
const sel=new Set(PROVIDERS);
const tip=document.getElementById('tip');
function showTip(e,html){{tip.innerHTML=html;tip.style.opacity=1;moveTip(e);}}
function moveTip(e){{tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px';}}
function hideTip(){{tip.style.opacity=0;}}
const proj=(lon,lat)=>[(lon+180)/360*720,(90-lat)/180*340];

const centroidOf=name=>{{const ne=ALIAS[name]||name;return WORLD.centroids[ne]||CENTROIDS[name]||null;}};
function renderMap(){{
  const svg=document.getElementById('map');
  const ev=DATA.filter(d=>sel.has(d.p));
  const byC={{}};
  ev.forEach(d=>{{(byC[d.c]=byC[d.c]||[]).push(d);}});
  let parts=[];
  // reference land layer (Natural Earth 110m, public domain)
  WORLD.countries.forEach(c=>{{
    const d=c.p.map(ring=>'M'+ring.map(pt=>{{const q=proj(pt[0],pt[1]);return q[0].toFixed(1)+' '+q[1].toFixed(1);}}).join('L')+'Z').join(' ');
    parts.push(`<path class="land" d="${{d}}"/>`);
  }});
  // bubbles at country centroids
  const mapped=Object.entries(byC).filter(([c])=>centroidOf(c));
  let shown=0;
  const max=Math.max(1,...mapped.map(([,a])=>a.length));
  const R=n=>4+Math.sqrt(n/max)*20;
  mapped.sort((a,b)=>a[1].length-b[1].length).forEach(([c,arr])=>{{
    const ll=centroidOf(c),q=proj(ll[0],ll[1]),r=R(arr.length);shown+=arr.length;
    const bd={{}};arr.forEach(d=>bd[d.p]=(bd[d.p]||0)+1);
    const brk=PROVIDERS.filter(p=>bd[p]).map(p=>`${{p}}: ${{bd[p]}}`).join(', ');
    parts.push(`<circle class="bub" cx="${{q[0].toFixed(1)}}" cy="${{q[1].toFixed(1)}}" r="${{r.toFixed(1)}}" data-t="<b>${{c}}</b> — ${{arr.length}} operations<br>${{brk}}"/>`);
    if(arr.length>=3)parts.push(`<text class="blab" x="${{q[0].toFixed(1)}}" y="${{(q[1]+3).toFixed(1)}}">${{arr.length}}</text>`);
  }});
  svg.innerHTML=parts.join('');
  svg.querySelectorAll('.bub').forEach(el=>{{el.onmousemove=e=>showTip(e,el.dataset.t);el.onmouseleave=hideTip;}});
  const unmapped=ev.length-shown;
  document.getElementById('maplegend').innerHTML=
    `<span class="lg">${{shown}} operations shown`+(unmapped>0?` · ${{unmapped}} without a mapped country`:``)+`</span>`;
}}

function renderTimeline(){{
  const ev=DATA.filter(d=>sel.has(d.p)&&d.d);
  const el=document.getElementById('timeline');
  if(!ev.length){{el.innerHTML='<div class="note">No takedowns for the selected companies.</div>';document.getElementById('tlaxis').innerHTML='';return;}}
  const ds=ev.map(d=>new Date(d.d).getTime());
  const lo=Math.min(...ds),hi=Math.max(...ds),span=Math.max(1,hi-lo);
  const lanes=PROVIDERS.filter(p=>sel.has(p));
  let h='';
  lanes.forEach(p=>{{
    const marks=ev.filter(d=>d.p===p).map(d=>{{
      const left=100*(new Date(d.d).getTime()-lo)/span;
      const t=`<b>${{d.a}}</b><br>${{p}} · ${{d.c}} · ${{d.d}}`;
      return `<span class="tlmark" style="left:${{left}}%;background:var(--series-${{PCOLOR[p]}})" data-t="${{t.replace(/"/g,'&quot;')}}"></span>`;
    }}).join('');
    h+=`<div class="tllane"><span class="tlp">${{p}}</span><span class="tltrack">${{marks}}</span></div>`;
  }});
  el.innerHTML=h;
  el.querySelectorAll('.tlmark').forEach(m=>{{m.onmousemove=e=>showTip(e,m.dataset.t);m.onmouseleave=hideTip;}});
  const f=t=>new Date(t).toISOString().slice(0,10);
  document.getElementById('tlaxis').innerHTML=`<span>${{f(lo)}}</span><span>${{f(hi)}}</span>`;
}}

function render(){{renderMap();renderTimeline();}}
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{{
  const p=c.dataset.p;if(sel.has(p)){{sel.delete(p);c.classList.remove('on');}}
  else{{sel.add(p);c.classList.add('on');}}render();}});
document.getElementById('all').onclick=()=>{{PROVIDERS.forEach(p=>sel.add(p));
  document.querySelectorAll('.chip').forEach(c=>c.classList.add('on'));render();}};
document.getElementById('none').onclick=()=>{{sel.clear();
  document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));render();}};
window.addEventListener('mousemove',e=>{{if(tip.style.opacity==1)moveTip(e);}});
render();
</script>
</body></html>"""


if __name__ == "__main__":
    main()
