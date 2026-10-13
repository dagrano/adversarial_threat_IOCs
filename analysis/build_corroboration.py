#!/usr/bin/env python3
"""Build a self-contained cross-source corroboration + actor-timeline page.

Mirrors build_dashboard.py / build_query.py: stdlib only, embeds the resolved
index as JSON into one offline HTML file (analysis/out/corroboration.html).
Ranks named actors by how many independent providers reported them, and draws a
per-actor reporting timeline (each report on its date, sized by indicator count,
coloured by actor, linked to its source). Light/dark aware.
"""
import csv, json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def load():
    p = os.path.join(OUT, "normalized_indicators.csv")
    rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    actors = {}
    reports = collections.defaultdict(int)
    for r in rows:
        if r.get("actor_is_named") != "True" or not r.get("actor_id"):
            continue
        aid = r["actor_id"]
        a = actors.setdefault(aid, {"name": r.get("actor_name") or aid,
                                    "country": r.get("actor_country", ""),
                                    "providers": set(), "nrows": 0, "reports": set()})
        a["providers"].add(r["source_provider"]); a["nrows"] += 1
        key = (aid, r["source_provider"], r["source_report"], r["report_date"], r["source_url"])
        a["reports"].add((r["source_provider"], r["source_report"], r["report_date"], r["source_url"]))
        reports[key] += 1
    ACTORS = []
    for aid, a in actors.items():
        ACTORS.append({"id": aid, "name": a["name"], "country": a["country"],
                       "providers": sorted(a["providers"]), "np": len(a["providers"]),
                       "nrows": a["nrows"], "nreports": len(a["reports"])})
    ACTORS.sort(key=lambda x: (-x["np"], -x["nreports"], -x["nrows"], x["name"].lower()))
    REPORTS = [{"aid": k[0], "prov": k[1], "title": k[2], "date": k[3], "url": k[4], "n": n}
               for k, n in reports.items()]
    return ACTORS, REPORTS


def main():
    os.makedirs(OUT, exist_ok=True)
    ACTORS, REPORTS = load()
    html = (TEMPLATE
            .replace("__ACTORS__", json.dumps(ACTORS, separators=(",", ":")))
            .replace("__REPORTS__", json.dumps(REPORTS, separators=(",", ":"))))
    out = os.path.join(OUT, "corroboration.html")
    open(out, "w", encoding="utf-8").write(html)
    nmulti = sum(1 for a in ACTORS if a["np"] >= 2)
    print(f"Wrote {out} ({len(ACTORS)} named actors, {nmulti} reported by >=2 providers)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Corroboration</title>
<style>
/* Layout: a ranked "most-corroborated actors" list that drives a per-actor
   reporting timeline below. Palette reuses the corpus dashboard's system. */
:root{
  color-scheme:light dark;
  --plane:#f9f9f7; --surface-1:#fcfcfb; --surface-2:#eef0f2;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --muted:#898781;
  --grid:#e1e0d9; --border:rgba(11,11,11,.10); --accent:#2a78d6; --track:#eef0f2;
  --mono:ui-monospace,Menlo,"SFMono-Regular",Consolas,monospace;
  /* categorical actor colours (validated; fixed order, never cycled) */
  --a1:#2a78d6; --a2:#eb6834; --a3:#1baf7a; --a4:#eda100; --a5:#e05b8c; --a6:#9b5de5;
}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12); --accent:#3987e5; --track:#2c2c2a;
  --a1:#3987e5; --a2:#d95926; --a3:#199e70; --a4:#c98500; --a5:#d55181; --a6:#a06ee8;
  color-scheme:dark;
}}
:root[data-theme=dark]{
  --plane:#0d0d0d; --surface-1:#1a1a19; --surface-2:#2c2c2a;
  --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --border:rgba(255,255,255,.12); --accent:#3987e5; --track:#2c2c2a;
  --a1:#3987e5; --a2:#d95926; --a3:#199e70; --a4:#c98500; --a5:#d55181; --a6:#a06ee8;
  color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--plane);color:var(--text-primary);
  font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;
  padding:0 max(16px,env(safe-area-inset-left)) 44px max(16px,env(safe-area-inset-right))}
.wrap{max-width:1120px;margin:0 auto}
header.top{padding-block:20px 6px}
h1{font-size:21px;margin:0 0 2px;letter-spacing:-.01em}
.sub{color:var(--text-secondary);margin:0;font-size:13px}
.nav{font-size:12.5px;margin-top:6px} .nav a{color:var(--accent);text-decoration:none;margin-right:14px} .nav a:hover{text-decoration:underline}
.tog{position:absolute;top:env(safe-area-inset-top,0px);right:max(16px,env(safe-area-inset-right));
  margin-top:14px;background:var(--surface-1);color:var(--text-secondary);
  border:1px solid var(--border);border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px}
h2{font-size:15px;margin:24px 0 4px} .note{color:var(--muted);font-size:12px;margin:0 0 12px}
section{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:14px}

/* ranking */
.ctrlrow{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.seg{display:inline-flex;border:1px solid var(--border);border-radius:8px;overflow:hidden}
.seg button{background:var(--surface-1);color:var(--text-secondary);border:none;
  padding:5px 11px;font:inherit;font-size:12.5px;cursor:pointer;border-left:1px solid var(--border)}
.seg button:first-child{border-left:none}
.seg button.on{background:var(--accent);color:#fff}
.hint{color:var(--muted);font-size:12px;margin-left:auto}
.rank{display:flex;flex-direction:column;gap:3px}
.rrow{display:grid;grid-template-columns:200px 1fr auto;align-items:center;gap:10px;
  padding:5px 7px;border-radius:8px;cursor:pointer;border:1px solid transparent}
.rrow:hover{background:var(--surface-2)}
.rrow.sel{border-color:var(--border);background:var(--surface-2)}
.rname{display:flex;align-items:center;gap:7px;min-width:0}
.swatch{width:10px;height:10px;border-radius:3px;flex:none;background:var(--muted);opacity:.25}
.rrow.sel .swatch{opacity:1}
.rnm{font-weight:600;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rco{color:var(--muted);font-size:11px;white-space:nowrap}
.rtrack{height:16px;background:var(--track);border-radius:4px;position:relative;overflow:hidden}
.rfill{height:100%;background:var(--accent);border-radius:0 4px 4px 0;opacity:.85}
.provtags{display:flex;gap:3px;flex-wrap:wrap;margin-top:3px}
.ptag{font-size:9.5px;letter-spacing:.02em;text-transform:uppercase;color:var(--muted);
  border:1px solid var(--border);border-radius:4px;padding:0 4px;line-height:14px}
.rmeta{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.rmeta b{font-size:16px} .rmeta span{color:var(--muted);font-size:11px}

/* timeline */
.legend{display:flex;gap:14px;flex-wrap:wrap;margin:0 0 8px;font-size:12.5px}
.lg{display:inline-flex;align-items:center;gap:6px;color:var(--text-primary)}
.lg i{width:11px;height:11px;border-radius:3px;display:inline-block}
.lg b{font-variant-numeric:tabular-nums;color:var(--text-secondary);font-weight:600}
.empty{color:var(--muted);font-size:13px;padding:18px 2px}
#tl{width:100%;height:auto;display:block;overflow:visible}
.lane-bg{fill:var(--surface-2);opacity:.5}
.lanelab{fill:var(--text-primary);font-size:11.5px;font-weight:600}
.axis text{fill:var(--muted);font-size:10.5px} .axis line{stroke:var(--grid);stroke-width:1}
.mk{stroke:var(--surface-1);stroke-width:2;cursor:pointer}
.mk:hover{stroke:var(--text-primary)}
.sizekey{color:var(--muted);font-size:11.5px;margin-top:6px;display:flex;align-items:center;gap:7px}
.sizekey svg{vertical-align:middle}
#tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);
  border:1px solid var(--border);border-radius:8px;padding:7px 10px;font-size:12px;opacity:0;
  transition:opacity .08s;z-index:9;max-width:300px;box-shadow:0 4px 16px rgba(0,0,0,.18)}
#tip .tt{font-weight:600;margin-bottom:2px} #tip .tm{color:var(--text-secondary)}
#tip .tl{color:var(--accent);margin-top:3px}
.foot{color:var(--muted);font-size:11.5px;margin-top:16px}
.foot code{font-family:var(--mono)}
@media(max-width:620px){.rrow{grid-template-columns:140px 1fr auto}}
</style></head>
<body>
<button class="tog" onclick="var r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'">◐ theme</button>
<div class="wrap">
<header class="top">
  <h1>Cross-source corroboration</h1>
  <p class="sub">Named actors ranked by how many independent providers reported them — the corpus's core signal. Select actors to chart their reporting history.</p>
  <div class="nav"><a href="index.html">← Dashboard</a><a href="query.html">IOC Explorer →</a></div>
</header>

<h2>Most-corroborated actors</h2>
<section>
  <div class="ctrlrow">
    <div class="seg" id="minseg">
      <button data-n="2" class="on">≥2 providers</button>
      <button data-n="3">≥3</button>
      <button data-n="4">≥4</button>
      <button data-n="1">all named</button>
    </div>
    <div class="hint" id="rankhint"></div>
  </div>
  <div class="rank" id="rank"></div>
</section>

<h2>Actor reporting timeline</h2>
<section>
  <p class="note">Each marker is one report on its publication date, sized by the number of indicators it contributed, coloured by actor. Click a marker to open the source report. Pick up to 6 actors from the list above.</p>
  <div class="legend" id="legend"></div>
  <div id="tlwrap"><svg id="tl" role="img" aria-label="Actor reporting timeline"></svg></div>
  <div class="sizekey" id="sizekey"></div>
</section>

<p class="foot">Generated by <code>analysis/build_corroboration.py</code> from <code>analysis/out/normalized_indicators.csv</code>. Actor identity is resolved through <code>analysis/aliases.csv</code>; "providers" counts distinct reporting organisations, so a shared named actor across providers is strong corroboration. PDF/blog-extracted rows are leads — verify against the source before operational use.</p>
</div>
<div id="tip"></div>

<script>
const ACTORS=__ACTORS__, REPORTS=__REPORTS__;
const COLORS=['--a1','--a2','--a3','--a4','--a5','--a6'], MAXSEL=6;
const byId={}; ACTORS.forEach(a=>byId[a.id]=a);
const repByActor={}; for(const r of REPORTS){(repByActor[r.aid]=repByActor[r.aid]||[]).push(r);}
let minN=2, selected=[];
const PROVLBL={anthropic:'ANTH',openai:'OAI',meta:'META',google:'GTIG',tiktok:'TT',x:'X',microsoft:'MSFT',mandiant:'MND',dfrlab:'DFR',graphika:'GRPH',eu_disinfolab:'EUDL',cisa:'CISA',fbi:'FBI'};
const cssv=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// default selection: top 2 most-corroborated
selected=ACTORS.slice(0,2).map(a=>a.id);

function colorFor(aid){const i=selected.indexOf(aid);return i<0?null:cssv(COLORS[i]);}

function renderRank(){
  const list=ACTORS.filter(a=>a.np>=minN);
  const maxNp=list.length?list[0].np:1;
  document.getElementById('rankhint').textContent=list.length+' actors';
  const el=document.getElementById('rank'); el.innerHTML='';
  if(!list.length){el.innerHTML='<div class="empty">No named actors meet this threshold.</div>';return;}
  for(const a of list){
    const sel=selected.includes(a.id);
    const col=sel?colorFor(a.id):null;
    const row=document.createElement('div');
    row.className='rrow'+(sel?' sel':''); row.tabIndex=0; row.dataset.id=a.id;
    const tags=a.providers.map(p=>'<span class="ptag">'+(PROVLBL[p]||p)+'</span>').join('');
    row.innerHTML=
      '<div class="rname"><span class="swatch" style="'+(col?'background:'+col+';opacity:1':'')+'"></span>'+
        '<span style="min-width:0"><span class="rnm">'+esc(a.name)+'</span>'+
        (a.country?' <span class="rco">'+esc(a.country)+'</span>':'')+'</span></div>'+
      '<div><div class="rtrack"><span class="rfill" style="width:'+(100*a.np/maxNp)+'%'+(col?';background:'+col:'')+'"></span></div>'+
        '<div class="provtags">'+tags+'</div></div>'+
      '<div class="rmeta"><b>'+a.np+'</b> <span>providers</span><br><span>'+a.nreports+' reports · '+a.nrows+' rows</span></div>';
    row.onclick=()=>toggle(a.id); row.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle(a.id);}};
    el.appendChild(row);
  }
}
function toggle(aid){
  const i=selected.indexOf(aid);
  if(i>=0) selected.splice(i,1);
  else { if(selected.length>=MAXSEL){flash();return;} selected.push(aid); }
  renderRank(); renderTimeline();
}
let flashT; function flash(){const h=document.getElementById('rankhint');const o=h.textContent;h.textContent='up to '+MAXSEL+' actors — deselect one first';clearTimeout(flashT);flashT=setTimeout(()=>renderRank(),1800);}

function renderLegend(){
  const el=document.getElementById('legend'); el.innerHTML='';
  if(!selected.length){el.innerHTML='<span class="note" style="margin:0">Select actors from the list above.</span>';return;}
  selected.forEach((aid,i)=>{
    const a=byId[aid], col=cssv(COLORS[i]);
    const reps=repByActor[aid]||[]; const tot=reps.reduce((s,r)=>s+r.n,0);
    const s=document.createElement('span'); s.className='lg';
    s.innerHTML='<i style="background:'+col+'"></i>'+esc(a.name)+' <b>'+reps.length+' reports · '+a.np+' providers · '+tot.toLocaleString()+' rows</b>';
    el.appendChild(s);
  });
}

const SVGNS='http://www.w3.org/2000/svg';
function el(tag,attrs){const n=document.createElementNS(SVGNS,tag);for(const k in attrs)n.setAttribute(k,attrs[k]);return n;}
function renderTimeline(){
  renderLegend();
  const svg=document.getElementById('tl'); svg.innerHTML='';
  const sizekey=document.getElementById('sizekey'); sizekey.innerHTML='';
  if(!selected.length){svg.removeAttribute('viewBox');svg.style.height='0';return;}
  const reps=[]; selected.forEach((aid)=>{(repByActor[aid]||[]).forEach(r=>reps.push(r));});
  if(!reps.length){svg.style.height='0';return;}
  const dates=reps.map(r=>Date.parse(r.date)).filter(x=>!isNaN(x));
  let dmin=Math.min(...dates), dmax=Math.max(...dates); if(dmin===dmax){dmin-=2.6e9;dmax+=2.6e9;}
  const W=1080, padL=120, padR=26, padT=10, laneH=48, axisH=26;
  const H=padT+selected.length*laneH+axisH;
  svg.setAttribute('viewBox','0 0 '+W+' '+H); svg.style.height='auto';
  const x=t=>padL+(padR>0? (W-padL-padR):0)*(Date.parse(t)-dmin)/(dmax-dmin||1);
  const maxN=Math.max(...reps.map(r=>r.n),1);
  const rad=n=>{const r=5+17*Math.sqrt(n/maxN);return Math.max(5,Math.min(22,r));};
  // year gridlines
  const g=el('g',{class:'axis'}); svg.appendChild(g);
  const y0=new Date(dmin).getUTCFullYear(), y1=new Date(dmax).getUTCFullYear();
  for(let y=y0;y<=y1+1;y++){
    const t=Date.UTC(y,0,1); if(t<dmin-1e10||t>dmax+1e10)continue;
    const px=padL+(W-padL-padR)*(t-dmin)/(dmax-dmin||1);
    if(px<padL-1||px>W-padR+1)continue;
    g.appendChild(el('line',{x1:px,y1:padT,x2:px,y2:padT+selected.length*laneH}));
    const tx=document.createElementNS(SVGNS,'text'); tx.setAttribute('x',px); tx.setAttribute('y',H-8); tx.setAttribute('text-anchor','middle'); tx.setAttribute('class','axis'); tx.textContent=y;
    g.appendChild(tx);
  }
  // lanes
  selected.forEach((aid,li)=>{
    const col=cssv(COLORS[li]); const a=byId[aid];
    const ly=padT+li*laneH;
    svg.appendChild(el('rect',{x:padL-6,y:ly+5,width:W-padL-padR+12,height:laneH-10,rx:7,class:'lane-bg'}));
    const lab=document.createElementNS(SVGNS,'text'); lab.setAttribute('x',8); lab.setAttribute('y',ly+laneH/2+4); lab.setAttribute('class','lanelab'); lab.setAttribute('fill',col);
    lab.textContent=a.name.length>17?a.name.slice(0,16)+'…':a.name; svg.appendChild(lab);
    const reps2=(repByActor[aid]||[]).slice().sort((p,q)=>p.n-q.n); // big on top
    for(const r of reps2){
      const cx=x(r.date), cy=ly+laneH/2;
      const link=el('a',{}); link.setAttributeNS('http://www.w3.org/1999/xlink','href',r.url); link.setAttribute('target','_blank'); link.setAttribute('rel','noopener');
      const c=el('circle',{cx:cx,cy:cy,r:rad(r.n),fill:col,'fill-opacity':0.78,class:'mk'});
      c.addEventListener('mousemove',e=>showTip(e,a.name,r));
      c.addEventListener('mouseleave',hideTip);
      link.appendChild(c); svg.appendChild(link);
    }
  });
  // size key
  sizekey.innerHTML='Marker size = indicators contributed by that report (√ scale; max '+maxN.toLocaleString()+'). Click a marker to open its source.';
}
function showTip(e,aname,r){
  const t=document.getElementById('tip');
  t.innerHTML='<div class="tt">'+esc(aname)+'</div>'+
    '<div class="tm">'+esc((PROVLBL[r.prov]||r.prov))+' · '+esc(r.date)+' · <b>'+r.n.toLocaleString()+'</b> indicator'+(r.n===1?'':'s')+'</div>'+
    '<div>'+esc(r.title.length>80?r.title.slice(0,79)+'…':r.title)+'</div>'+
    '<div class="tl">open report →</div>';
  t.style.opacity=1; const pad=14;
  let L=e.clientX+pad, T=e.clientY+pad;
  const w=t.offsetWidth,h=t.offsetHeight;
  if(L+w>innerWidth-8)L=e.clientX-w-pad; if(T+h>innerHeight-8)T=e.clientY-h-pad;
  t.style.left=L+'px'; t.style.top=T+'px';
}
function hideTip(){document.getElementById('tip').style.opacity=0;}

document.querySelectorAll('#minseg button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#minseg button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); minN=+b.dataset.n; renderRank();
});
renderRank(); renderTimeline();
new MutationObserver(()=>{if(selected.length)renderTimeline();}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
