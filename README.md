# Adversarial Threat IOCs

A community-maintained, machine-readable collection of the indicators and
tradecraft published in adversarial-threat reporting across tech companies and
security investigations. Every report is normalized into one flat CSV schema so
you can search, diff, and import the data into a SIEM, TIP, or a spreadsheet
without re-reading a stack of PDFs.

**Current sources:** Meta, OpenAI, Anthropic, Google (GTIG), TikTok, and X.
**Roadmap:** Mandiant's classic APT IOC catalog and vetted OSINT /
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
| Meta | `facebook/threat-research` GitHub repo — classic IOC tables (2020–2023) + Online Operations Kill Chain files for CIB takedowns (2023–present) | **Full history**, normalized from all 68 source CSVs |
| Anthropic | Per-case-study indicator tables inside each report PDF; recent editions are IOC-rich | March 2025, August 2025, September 2026 |
| OpenAI | Operation write-ups in report PDFs; very few hard IOCs by design | June 2025, October 2025 (older editions tracked as pending) |
| Google (GTIG) | Actor-by-actor AI-misuse reporting; the AI Threat Tracker adds malware families | *Adversarial Misuse of Generative AI* (Jan 2025), *AI Threat Tracker* (Feb 2026) |
| TikTok | Covert Influence Operations transparency disclosures; behavioral, few hard IOCs | Jan–Apr 2024 aggregate + examples (**partial** — per-network detail behind a JS transparency center) |
| X (Twitter) | Historical state-linked IO archive (2018–2021), discontinued after 2022 | **Account-level attribution only** (no tweet content): 25 disclosed networks with country + account counts |

Current size: **11,600+ rows**. Rebuild stats print when you run
`scripts/build_master.py`.

X rows use `indicator_type = asset_count` (e.g. "4,779 accounts") because X
published account datasets, not atomic IOCs; per the corpus's scope these
capture network-level attribution, not individual tweets.

## Layout

```
data/
  anthropic/   one CSV per report  (YYYY-MM-DD_slug.csv)
  openai/
  meta/
  google/
  tiktok/
  x/
dist/
  indicators.csv        generated master (all rows, sorted) — the file to query
schema/
  fields.md             the 16-field schema, documented
  indicator_types.csv   controlled vocabulary for indicator_type
  actor_types.csv       controlled vocabulary for actor_type
  ttp_frameworks.csv    controlled vocabulary for ttp_framework
scripts/
  normalize_meta.py             regenerate data/meta from a repo clone
  backfill_anthropic_openai.py  regenerate data/anthropic + data/openai
  backfill_google_tiktok_x.py   regenerate data/google + data/tiktok + data/x
  build_master.py               concat data/**/*.csv -> dist/indicators.csv
  validate.py                   schema + vocabulary check (CI gate)
  check_new_reports.py          monthly: find un-ingested reports
sources.json          manifest of every known report + ingest status
```

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
- **Anthropic / OpenAI rows** are extracted from report PDFs and should be
  **spot-checked against `source_url`** before operational blocking. PDF table
  extraction can transpose a character in a hash or IP. Treat them as leads,
  verify before enforcement.
- No indicator here is a substitute for your own validation. This is a research
  and triage corpus.

## Keeping it current

Backfill is a one-time job; after that the corpus is maintained monthly. Run:

```bash
python3 scripts/check_new_reports.py
```

It diffs Meta's live GitHub tree against `data/meta/`, lists anything still
marked `pending` in `sources.json`, and surfaces candidate new report links on
the Anthropic/OpenAI listing pages for review. Ingest anything new, flip its
status in `sources.json`, rebuild, and open a PR. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## License & attribution

MIT (see `LICENSE`) — chosen to match Meta's upstream `threat-research`
repository, which publishes its data under MIT. The underlying indicators
belong to their respective publishers (Anthropic, OpenAI, Meta); this project
redistributes them for defensive research with attribution via `source_url`,
and the `NOTICE` file retains Meta's copyright and credits all three sources.
If you are one of these publishers and want a change, open an issue.
