# Adversarial Threat IOCs

A community-maintained, machine-readable collection of the indicators and
tradecraft published in adversarial-threat reporting across tech companies and
security investigations. Every report is normalized into one flat CSV schema so
you can search, diff, and import the data into a SIEM, TIP, or a spreadsheet
without re-reading a stack of PDFs.

**Current sources:** Meta, OpenAI, Anthropic, Google (GTIG), TikTok, X,
Microsoft (MSTIC/MTAC), Mandiant, DFRLab, Graphika, EU DisinfoLab, and
government advisories (CISA, FBI). NCSC is tracked but has no in-scope report
yet (its public actor reporting is cyber-espionage, outside this corpus's
influence-operations / AI-misuse scope).
**Roadmap:** deeper government-advisory coverage and additional vetted OSINT /
security-vendor investigations. Sources are an extensible vocabulary
(`schema/providers.csv`) — adding one is a one-line change, then drop CSVs
under `data/<provider>/`.

> **Scope note, read this first.** These sources do **not** publish indicators
> the way a classic CTI vendor does. Meta's older files and Anthropic's and
> Google's recent reports carry real technical IOCs (domains, IPs, hashes,
> emails, malware families). But a large share of what these providers publish
> is *behavioral* — account attributions, coordinated-inauthentic-behavior
> patterns, and model-abuse TTPs — and OpenAI in particular states it shares
> hard technical indicators privately with industry partners rather than in the
> report. This corpus therefore captures **indicators and TTPs**, not IOCs
> alone, and is honest about which rows are which (see `indicator_type`).

## What's in it

| Provider | What they publish | Coverage here |
|---|---|---|
| Meta | `facebook/threat-research` GitHub repo — classic IOC tables (2020–2023) + Online Operations Kill Chain files for CIB takedowns (2023–present), **plus** the narrative quarterly/biannual Adversarial Threat Reports | **Full repo history** (68 source CSVs) + **13 narrative ATR editions** (2022–2025) |
| Anthropic | Per-case-study indicator tables inside each report PDF; recent editions are IOC-rich | March 2025, August 2025, September 2026 |
| OpenAI | Operation write-ups in report PDFs; very few hard IOCs by design | June 2025, October 2025 (older editions tracked as pending) |
| Google (GTIG) | Actor-by-actor AI-misuse reporting; the AI Threat Tracker adds malware families | *Adversarial Misuse of Generative AI* (Jan 2025), *AI Threat Tracker* (Feb 2026) |
| TikTok | Covert Influence Operations transparency disclosures; behavioral, few hard IOCs | Jan–Apr 2024 aggregate + examples (**partial** — per-network detail behind a JS transparency center) |
| X (Twitter) | Historical state-linked IO archive (2018–2021), discontinued after 2022 | **Account-level attribution only** (no tweet content): 25 disclosed networks with country + account counts |
| Microsoft (MSTIC/MTAC) | Influence-operations & AI-misuse reporting (Storm-#### networks, election IO, the AI-threat-actor taxonomy) | 7 reports (2023–2024): AI-threat-actor report, East Asia, Paris Olympics, US-election IO, Iran |
| Mandiant | Mandiant-bylined information-operations reporting | DRAGONBRIDGE (2022 midterms), Ghostwriter / UNC1151 (Belarus) |
| DFRLab | Atlantic Council influence-operation investigations | Doppelganger (2024, domain lists), Iranian election interference |
| Graphika | Influence-operation research reports | Spamouflage: *Goes to America* (2020), *The #Americans* (2024) |
| EU DisinfoLab | Disinformation / influence-operation investigations | Doppelganger (origin report, 2022), Indian Chronicles (Srivastava Group) |
| CISA / FBI | Government advisories — influence-ops & AI-misuse / state-linked only | CISA: Emennet Pasargad (domains, IPs, hashes, AI-tool misuse); FBI/DOJ: Doppelganger 32-domain seizure |

Data explorer tools and visualization here: https://dagrano.github.io/adversarial_threat_IOCs/

Current size: **11,800+ rows** across 12 sources. Rebuild stats print when you
run `scripts/build_master.py`.

Scope for the newer sources (Microsoft, Mandiant, DFRLab, Graphika, EU
DisinfoLab, CISA/FBI/NCSC) is **influence operations and AI-misuse only** —
generic ransomware/CVE advisories and pure cyber-espionage are out of scope.
Government joint advisories are keyed to the lead agency, with co-authors noted
in `description`.

X rows use `indicator_type = asset_count` (e.g. "4,779 accounts") because X
published account datasets, not atomic IOCs; per the corpus's scope these
capture network-level attribution, not individual tweets.

### Two Meta veins, tagged by `source_kind`

The build derives a **`source_kind`** column (in `dist/indicators.csv`, not in
the per-file schema — it comes from the row's directory):

- **`ioc`** — a row carrying a concrete released indicator (everything in
  `data/meta/` and every other provider's IOC drop).
- **`report`** — a per-network row from a provider's *narrative* report where
  the network was disclosed but **no machine indicators were released**. Today
  this is the Meta narrative ATRs in `data/meta-reports/`.

This makes "where did Meta report on an actor but release no IOCs?" a direct
filter (IOC Explorer → *Source kind → Narrative reports*), and keeps the two
veins honest about corroboration: because both carry `source_provider = meta`,
an actor appearing in a Meta IOC drop **and** a Meta narrative report still
counts Meta **once** in the cross-source view — no false corroboration.

## Layout

```
data/
  anthropic/   one CSV per report  (YYYY-MM-DD_slug.csv)
  openai/  meta/  google/  tiktok/  x/
  microsoft/  mandiant/  dfrlab/  graphika/  eu_disinfolab/  cisa/  fbi/
  meta-reports/  hand-curated Meta narrative ATR networks (source_kind=report)
                 NOT regenerated by normalize_meta.py — edit the CSVs directly
dist/
  indicators.csv        generated master (all rows, sorted) — the file to query
schema/
  fields.md             the 16-field schema, documented
  indicator_types.csv   controlled vocabulary for indicator_type
  actor_types.csv       controlled vocabulary for actor_type
  ttp_frameworks.csv    controlled vocabulary for ttp_framework
  providers.csv         controlled vocabulary for source_provider
scripts/
  normalize_meta.py             regenerate data/meta from a repo clone
  build_master.py               concat data/**/*.csv -> dist/indicators.csv
  validate.py                   schema + vocabulary check (CI gate)
  check_new_reports.py          monthly: find un-ingested reports
analysis/
  aliases.csv           hand-curated alias -> canonical actor map
  build_index.py        -> out/normalized_indicators.csv (resolved actors)
  build_dashboard.py    -> out/dashboard.html (overview, map, timeline)
  build_query.py        -> out/query.html  (IOC Explorer: search + filter)
  build_corroboration.py -> out/corroboration.html (cross-source view + actor timeline)
sources.json          manifest of every known report + ingest status
```

## Web tools (GitHub Pages)

Three self-contained pages are rebuilt by CI on every push and served from
GitHub Pages:

- **Dashboard** (`index.html`) — overview tiles, origin-country map,
  corroboration heatmap, takedown timeline.
- **IOC Explorer** (`query.html`) — search any selector and filter by origin
  country, provider, and indicator type; export the filtered set as CSV.
- **Cross-source corroboration** (`corroboration.html`) — ranks named actors by
  how many independent providers reported them, and draws a per-actor
  **reporting timeline**: each report on its date, sized by indicator count,
  colour-coded by actor, linked to its source. This is where the corpus's main
  value shows — e.g. *Doppelganger* reported by seven independent sources, or
  the same operation surfacing under different vendor names once the alias map
  reconciles them.

## The schema

Every row is one indicator (or one TTP summary) attributed to one actor in one
report. Columns, in order:

`actor, actor_type, source_provider, source_report, report_date, source_url,
indicator_type, indicator_value, country, target_country, target_sector, ttp,
ttp_framework, confidence, description, date_added`

Full field definitions and the controlled vocabularies are in
[`schema/fields.md`](schema/fields.md). Indicator values are kept **defanged**
(`[.]`) exactly as most sources publish them.

## Using it

```bash
# rebuild the master file from the per-report CSVs
python3 scripts/build_master.py

# hard network IOCs only (drop behavioral/TTP rows), for a blocklist
python3 - <<'PY'
import csv
keep = {"domain","url","ipv4","ipv6","sha256","sha1","md5","email","onion_domain"}
rows = [r for r in csv.DictReader(open("dist/indicators.csv"))
        if r["indicator_type"] in keep]
with open("dist/hard_iocs.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(len(rows),"hard IOCs")
PY
```

Because it's flat CSV, `grep`, `csvkit`, `pandas`, Excel, and most TIPs read it
directly. Each row carries its `source_url`, so any indicator is one click from
its source report.

## Data quality & provenance

- **Meta rows** are normalized programmatically from the source CSVs — high
  fidelity.
- **Government advisory rows** (CISA, FBI) carry authoritative hard IOCs —
  seized domains, IPs, file hashes — but the advisories themselves say to vet
  indicators before blocking.
- **PDF / blog-extracted rows** (Anthropic, OpenAI, Google, Microsoft, and the
  IO researchers) should be **spot-checked against `source_url`** before
  operational blocking — extraction can transpose a character in a hash or IP.
  Treat them as leads, verify before enforcement. Many IO-research rows are
  actor/TTP/persona summaries (confidence left blank), not atomic IOCs.
- **Cross-source corroboration** is a built-in quality signal: when independent
  providers surface the same indicator or actor, confidence rises. `analysis/`
  computes this (overlaps, the actor×provider matrix, linked-op clusters), and
  `corroboration.html` visualises it.
- No indicator here is a substitute for your own validation. This is a research
  and triage corpus.

## Keeping it current

Backfill is a one-time job; after that the corpus is maintained monthly. Run:

```bash
python3 scripts/check_new_reports.py
```

It diffs Meta's live GitHub tree against `data/meta/`, checks the Meta
narrative ATR listing for an edition newer than the latest in
`sources.json → providers.meta.atr_reports` (Meta publishes these
**~twice-annually**), lists anything still marked `pending` in `sources.json`,
and surfaces candidate new report links on the other providers' listing pages
for review. Ingest anything new — for a new Meta narrative ATR, add its
networks as `data/meta-reports/<date>_<slug>.csv` (`source_kind` is derived
automatically from the path) and append the edition to `atr_reports` — flip
status in `sources.json`, rebuild, and open a PR. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## License & attribution

MIT (see `LICENSE`) — chosen to match Meta's upstream `threat-research`
repository, which publishes its data under MIT. The underlying indicators
belong to their respective publishers (Meta, OpenAI, Anthropic, Google,
Microsoft, Mandiant, DFRLab, Graphika, EU DisinfoLab, CISA/FBI, and the
others); this project redistributes them for defensive research with
attribution via `source_url`, and the `NOTICE` file retains the upstream
copyrights and credits. If you are one of these publishers and want a change,
open an issue.
