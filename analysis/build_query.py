#!/usr/bin/env python3
"""Build a self-contained query page over dist/indicators.csv.

Mirrors build_dashboard.py: stdlib only, embeds the corpus as JSON into one
offline HTML file (analysis/out/query.html) with no external requests. Filter
by origin country, provider and indicator type, and free-text search across
actor / indicator / description / targeting. Light/dark aware.
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")

COLS = ["actor", "actor_type", "source_provider", "source_report", "report_date",
        "source_url", "indicator_type", "indicator_value", "country",
        "target_country", "target_sector", "ttp", "ttp_framework", "confidence",
        "description", "date_added"]

HARD = ["domain", "url", "ipv4", "ipv6", "sha256", "sha1", "md5", "email",
        "onion_domain", "crypto_wallet"]


def load():
    p = os.path.join(ROOT, "dist", "indicators.csv")
    rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    # emit as array-of-arrays (column order = COLS) to keep the payload small
    return [[r.get(c, "") for c in COLS] for r in rows]


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = load()
    countries = sorted({r[COLS.index("country")] for r in rows if r[COLS.index("country")]})
    types = sorted({r[COLS.index("indicator_type")] for r in rows if r[COLS.index("indicator_type")]})
    providers = sorted({r[COLS.index("source_provider")] for r in rows if r[COLS.index("source_provider")]})
    html = (TEMPLATE
            .replace("__COLS__", json.dumps(COLS, separators=(",", ":")))
            .replace("__ROWS__", json.dumps(rows, separators=(",", ":")))
            .replace("__COUNTRIES__", json.dumps(countries, separators=(",", ":")))
            .replace("__TYPES__", json.dumps(types, separators=(",", ":")))
            .replace("__PROVIDERS__", json.dumps(providers, separators=(",", ":")))
            .replace("__HARD__", json.dumps(HARD, separators=(",", ":")))
            .replace("__NROWS__", str(len(rows))))
    out = os.path.join(OUT, "query.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"Wrote {out} ({len(rows)} rows, {len(html)//1024} KB)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>IOC Explorer</title>
<style>
/* Layout: a sticky control rail over a dense, scannable results table.
   Palette + type reuse the corpus dashboard so the two pages read as one site. */
:root{
  color-scheme:light dark;
  --plane:#f9f9f7; --surface-1:#fcfcfb; --surface-2:#eef0f2;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --muted:#898781;
  --grid:#e1e0d9; --border:rgba(11,11,11,.10);
  --accent:#2a78d6; --good:#0ca30c; --warn:#eda100;
  --mono:ui-monospace,Menlo,"SFMono-Regular",Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12);
  --accent:#3987e5; --good:#2fb62f; --warn:#c98500; color-scheme:dark;
}}
:root[data-theme=dark]{
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12);
  --accent:#3987e5; --good:#2fb62f; --warn:#c98500; color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--plane);color:var(--text-primary);
  font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;
  padding:0 max(16px,env(safe-area-inset-left)) 40px max(16px,env(safe-area-inset-right))}
.wrap{max-width:1180px;margin:0 auto}
header.top{padding-block:20px 10px}
h1{font-size:21px;margin:0 0 2px;letter-spacing:-.01em}
.sub{color:var(--text-secondary);margin:0;font-size:13px}
.tog{position:absolute;top:env(safe-area-inset-top,0px);right:max(16px,env(safe-area-inset-right));
  margin-top:14px;background:var(--surface-1);color:var(--text-secondary);
  border:1px solid var(--border);border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px}

.controls{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;
  background:var(--plane);border-bottom:1px solid var(--border);
  padding-block:10px;margin-bottom:12px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end}
.field{display:flex;flex-direction:column;gap:3px;min-width:0}
.field label{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.search{flex:1 1 320px}
input[type=search],select{font:inherit;font-size:13px;color:var(--text-primary);
  background:var(--surface-1);border:1px solid var(--border);border-radius:8px;padding:8px 10px}
input[type=search]{width:100%}
input[type=search]:focus,select:focus{outline:2px solid var(--accent);outline-offset:0;border-color:var(--accent)}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{border:1px solid var(--border);background:var(--surface-1);color:var(--text-secondary);
  border-radius:999px;padding:6px 11px;font-size:12.5px;cursor:pointer;user-select:none}
.chip.on{color:#fff;background:var(--accent);border-color:var(--accent)}
.chip:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.toggle{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--text-secondary);cursor:pointer}
.actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-left:auto}
.btn{font:inherit;font-size:12.5px;background:var(--surface-1);color:var(--text-primary);
  border:1px solid var(--border);border-radius:8px;padding:7px 12px;cursor:pointer}
.btn:hover{border-color:var(--text-secondary)}
.btn.ghost{color:var(--text-secondary)}

.summary{display:flex;gap:18px;flex-wrap:wrap;align-items:baseline;margin:2px 0 10px;
  font-variant-numeric:tabular-nums}
.summary b{font-size:20px;font-weight:650} .summary span{color:var(--text-secondary);font-size:12.5px}

.tablewrap{overflow-x:auto;border:1px solid var(--border);border-radius:10px;background:var(--surface-1)}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{position:sticky;top:0;text-align:left;font-weight:600;color:var(--text-secondary);
  background:var(--surface-2);border-bottom:1px solid var(--grid);padding:8px 10px;white-space:nowrap}
td{padding:7px 10px;border-bottom:1px solid var(--grid);vertical-align:top}
tr:last-child td{border-bottom:none}
.ind{font-family:var(--mono);font-size:12px;word-break:break-all;max-width:360px}
.desc{color:var(--text-secondary);max-width:320px}
.pill{font-size:11px;padding:1px 7px;border-radius:9px;border:1px solid var(--border);white-space:nowrap}
.pill.hard{background:color-mix(in srgb,var(--good) 16%,transparent);color:var(--good);border-color:transparent}
.prov{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
a.src{color:var(--accent);text-decoration:none} a.src:hover{text-decoration:underline}
mark{background:color-mix(in srgb,var(--warn) 45%,transparent);color:inherit;border-radius:2px}
.empty{padding:40px 16px;text-align:center;color:var(--muted)}
.more{padding:10px;text-align:center;color:var(--muted);font-size:12px;border-top:1px solid var(--grid)}
.foot{color:var(--muted);font-size:11.5px;margin-top:16px}
.foot code{font-family:var(--mono)}
</style></head>
<body>
<button class="tog" onclick="var r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'">◐ theme</button>
<div class="wrap">
<header class="top">
  <h1>IOC Explorer</h1>
  <p class="sub">Search and filter the adversarial-threat IOC corpus — <span id="total"></span> indicators from Meta, OpenAI, Anthropic, Google, TikTok and X.</p>
</header>

<div class="controls">
  <div class="row">
    <div class="field search">
      <label for="q">Search selectors &amp; text</label>
      <input type="search" id="q" placeholder="domain, hash, actor, persona, keyword…" autocomplete="off" spellcheck="false">
    </div>
    <div class="field">
      <label for="country">Origin country</label>
      <select id="country"><option value="">All countries</option></select>
    </div>
    <div class="field">
      <label for="type">Indicator type</label>
      <select id="type"><option value="">All types</option></select>
    </div>
    <div class="actions">
      <label class="toggle"><input type="checkbox" id="hardonly"> hard IOCs only</label>
      <button class="btn" id="copy">Copy CSV</button>
      <button class="btn" id="download">Download CSV</button>
      <button class="btn ghost" id="reset">Reset</button>
    </div>
  </div>
  <div class="row" style="margin-top:9px">
    <div class="field" style="flex:1 1 auto">
      <label>Reporting provider</label>
      <div class="chips" id="provchips"></div>
    </div>
  </div>
</div>

<div class="summary" id="summary"></div>
<div class="tablewrap">
  <table>
    <thead><tr>
      <th>Actor</th><th>Type</th><th>Indicator</th><th>Origin</th>
      <th>Target</th><th>Provider</th><th>Report</th><th>Context</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="more" id="more" hidden></div>
</div>

<p class="foot">Each row links to its <code>source_url</code>. PDF/blog-extracted indicators (OpenAI, Google, Anthropic) are leads — verify against the source before operational blocking. Values are kept defanged (<code>[.]</code>) as published. Built by <code>analysis/build_query.py</code> from <code>dist/indicators.csv</code>.</p>
</div>

<script>
const COLS=__COLS__, ROWS=__ROWS__, COUNTRIES=__COUNTRIES__, TYPES=__TYPES__,
      PROVIDERS=__PROVIDERS__, HARD=new Set(__HARD__), NROWS=__NROWS__, CAP=600;
const ix={}; COLS.forEach((c,i)=>ix[c]=i);
document.getElementById('total').textContent=NROWS.toLocaleString()+' ';

// populate controls
const csel=document.getElementById('country');
for(const c of COUNTRIES){const o=document.createElement('option');o.value=c;o.textContent=c;csel.appendChild(o);}
const tsel=document.getElementById('type');
for(const t of TYPES){const o=document.createElement('option');o.value=t;o.textContent=t;tsel.appendChild(o);}
const provOn=new Set(PROVIDERS);
const pc=document.getElementById('provchips');
for(const p of PROVIDERS){
  const b=document.createElement('button');b.className='chip on';b.textContent=p;b.dataset.p=p;
  b.setAttribute('aria-pressed','true');
  b.onclick=()=>{if(provOn.has(p)){provOn.delete(p);b.classList.remove('on');b.setAttribute('aria-pressed','false');}
    else{provOn.add(p);b.classList.add('on');b.setAttribute('aria-pressed','true');}render();};
  pc.appendChild(b);
}

const SEARCH_COLS=['actor','indicator_value','description','source_report','target_country','target_sector','ttp','persona'].map(c=>ix[c]).filter(i=>i!=null);
const q=document.getElementById('q'), hardonly=document.getElementById('hardonly');
let matches=[];

function filtered(){
  const term=q.value.trim().toLowerCase();
  const terms=term?term.split(/\s+/):[];
  const country=csel.value, type=tsel.value, hard=hardonly.checked;
  const out=[];
  for(const r of ROWS){
    if(!provOn.has(r[ix.source_provider]))continue;
    if(country && r[ix.country]!==country)continue;
    if(type && r[ix.indicator_type]!==type)continue;
    if(hard && !HARD.has(r[ix.indicator_type]))continue;
    if(terms.length){
      let hay='';for(const c of SEARCH_COLS)hay+=' '+(r[c]||'');
      hay=hay.toLowerCase();
      let ok=true;for(const t of terms){if(hay.indexOf(t)<0){ok=false;break;}}
      if(!ok)continue;
    }
    out.push(r);
  }
  return out;
}

function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function hl(s,terms){s=esc(s);for(const t of terms){if(!t)continue;
  const re=new RegExp('('+t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','ig');s=s.replace(re,'<mark>$1</mark>');}return s;}

function render(){
  matches=filtered();
  const terms=q.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const actors=new Set(),countries=new Set();
  for(const r of matches){if(r[ix.actor])actors.add(r[ix.actor]);if(r[ix.country])countries.add(r[ix.country]);}
  document.getElementById('summary').innerHTML=
    '<span><b>'+matches.length.toLocaleString()+'</b> indicators</span>'+
    '<span><b>'+actors.size+'</b> actors</span>'+
    '<span><b>'+countries.size+'</b> origin countries</span>';
  const tb=document.getElementById('tbody'); tb.innerHTML='';
  if(!matches.length){tb.innerHTML='<tr><td colspan="8" class="empty">No indicators match these filters.</td></tr>';
    document.getElementById('more').hidden=true;return;}
  const show=matches.slice(0,CAP);
  const frag=document.createDocumentFragment();
  for(const r of show){
    const tr=document.createElement('tr');
    const hard=HARD.has(r[ix.indicator_type])?' hard':'';
    const url=r[ix.source_url];
    const rep=esc(r[ix.source_report])+(r[ix.report_date]?' <span class="prov">'+esc(r[ix.report_date])+'</span>':'');
    const srcLink=url?' · <a class="src" href="'+esc(url)+'" target="_blank" rel="noopener">source</a>':'';
    tr.innerHTML=
      '<td>'+hl(r[ix.actor],terms)+'</td>'+
      '<td><span class="pill'+hard+'">'+esc(r[ix.indicator_type])+'</span></td>'+
      '<td class="ind">'+hl(r[ix.indicator_value],terms)+'</td>'+
      '<td>'+esc(r[ix.country])+'</td>'+
      '<td>'+esc(r[ix.target_country])+'</td>'+
      '<td class="prov">'+esc(r[ix.source_provider])+'</td>'+
      '<td class="desc">'+rep+srcLink+'</td>'+
      '<td class="desc">'+hl(r[ix.description],terms)+'</td>';
    frag.appendChild(tr);
  }
  tb.appendChild(frag);
  const more=document.getElementById('more');
  if(matches.length>CAP){more.hidden=false;
    more.textContent='Showing first '+CAP+' of '+matches.length.toLocaleString()+' — narrow the filters or search to see the rest (export returns all '+matches.length.toLocaleString()+').';}
  else more.hidden=true;
}

function toCSV(){
  const q2=s=>{s=(s==null?'':''+s);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  const lines=[COLS.join(',')];
  for(const r of matches)lines.push(r.map(q2).join(','));
  return lines.join('\n');
}
document.getElementById('copy').onclick=async e=>{
  const b=e.target,old=b.textContent;
  try{await navigator.clipboard.writeText(toCSV());b.textContent='Copied '+matches.length+' rows';}
  catch(_){b.textContent='Copy failed';}
  setTimeout(()=>b.textContent=old,1600);
};
document.getElementById('download').onclick=()=>{
  const blob=new Blob([toCSV()],{type:'text/csv'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='ioc-query.csv';document.body.appendChild(a);a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},0);
};
document.getElementById('reset').onclick=()=>{
  q.value='';csel.value='';tsel.value='';hardonly.checked=false;
  provOn.clear();PROVIDERS.forEach(p=>provOn.add(p));
  document.querySelectorAll('.chip').forEach(b=>{b.classList.add('on');b.setAttribute('aria-pressed','true');});
  render();
};
let t;q.addEventListener('input',()=>{clearTimeout(t);t=setTimeout(render,120);});
csel.onchange=render;tsel.onchange=render;hardonly.onchange=render;
render();
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
