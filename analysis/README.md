# analysis/

Investigation tooling over the corpus. stdlib-only Python; each script writes a
plain CSV/JSON report under `analysis/out/`. Run everything from the repo root.

## Foundation (build this first — everything else reads its output)

```bash
python3 scripts/build_master.py          # ensure dist/indicators.csv is current
python3 analysis/build_index.py          # -> analysis/out/normalized_indicators.csv
python3 analysis/foundation_report.py    # -> quality report + first-look signals
```

### The two primitives

**`normalize.py` — indicator normalization.** `canonicalize(type, value)`
refangs (`evil[.]com` -> `evil.com`), lowercases, strips scheme/`www`/paths, and
assigns a match **class**. Two indicators are "the same" iff they share
`(class, key)`. Classes join related types on purpose — a URL host, a bare
domain, and an email domain all become class `netloc`, so a domain in a Meta
file matches a URL host in an Anthropic report. `parse_metric()` pulls
`117 Facebook accounts` -> `(117, "accounts")` for the impact analysis.

**`resolve.py` + `aliases.csv` — actor resolution.** The same network appears
under different names across providers (Meta's *Spamouflage …* == Google's
*DRAGONBRIDGE*; APT41 == Winnti). `aliases.csv` is a **hand-curated** map of
alias -> canonical actor; extend it as you find more. `resolve()` returns a
canonical id and whether the string was a *named* actor or one of Meta's
filename-derived per-report labels (`IRAN-BASED CIB NETWORK`) — kept distinct
(`is_named=False`) so later analyses can weight a shared named actor as strong
evidence and a shared generic label as weak.

`aliases.csv` is the file to grow. It's the highest-leverage, human-in-the-loop
part of the whole pipeline — every actor you correctly alias makes the linked-ops
analysis sharper. A combined label ("Vixen Panda (APT15) / Keyhole Panda (APT5)")
currently resolves to one canonical id; split such rows at ingest if you need both.

### Outputs

- `out/normalized_indicators.csv` — the master index: every row of
  `dist/indicators.csv` plus `ind_class, ind_key, ind_host, actor_id,
  actor_name, actor_country, actor_is_named, metric_n, metric_unit`.
- `out/actor_provider_matrix.csv` — each canonical actor × which providers
  report it (the corroboration seed; sort by `n_providers`).
- `out/hard_indicator_overlaps.csv` — every hard indicator seen under more than
  one actor or provider (the overlap seed).
- `out/foundation_report.json` — machine-readable coverage summary.

## Analyses (each reads the index; run after build_index.py)

```bash
python3 analysis/overlap.py         # #1 cross-dataset indicator overlap
python3 analysis/linked_ops.py      # #2 actor+infra graph + clusters
python3 analysis/impact.py          # #3 reach metrics by actor / country
python3 analysis/corroboration.py   # who is reported by how many providers
python3 analysis/timeline.py        # first/last seen per actor / country
```

- **`overlap.py`** — every normalized indicator seen under >1 actor or provider,
  tagged strong / medium / weak by indicator type. `out/overlap_indicators.csv`
  and a provider-pair summary. (First cross-provider hit: `newstop.africa`,
  shared by Meta and OpenAI.)
- **`linked_ops.py`** — bipartite actor↔indicator graph; `bridges` are indicators
  tying multiple actors, `components` are actor clusters joined by shared infra.
  Exports `out/linked_ops.graphml` for Gephi/Cytoscape. Benign platform hubs are
  excluded before clustering (see below) and listed in `out/linked_ops_hubs.csv`.
  (A STIX exporter can be added here later.)
- **`impact.py`** — reach metrics from `asset_count` rows plus numbers parsed out
  of `description` (followers, ad spend, accounts/pages/groups), summed by actor
  and origin country. Coverage is sparse — totals are lower bounds, not
  platform-complete.
- **`corroboration.py`** — named-actor×provider and country×provider matrices.
  More providers = more corroborated.
- **`timeline.py`** — first/last seen, span, and provider count per actor and
  country. Separates persistent operations from one-offs.

## Dashboard

```bash
python3 analysis/build_dashboard.py     # -> out/dashboard.html (self-contained)
```

One offline HTML file with all data embedded (no external requests): overview
tiles, a country×provider corroboration heatmap, account-reach bars, the shared-
indicator table, linked-op clusters, and the named-actor timeline. Light/dark
aware, opens by double-click or serves from GitHub Pages.

## Hub / stop-list filter

`stoplist.txt` lists benign shared platforms (youtube.com, t.me, tiktok.com, …).
Both `overlap.py` and `linked_ops.py` drop these — an indicator on the stoplist,
or (for clustering) one shared by ≥ `DEGREE_CAP` actors, is treated as a hub, not
attributable infrastructure, so it can't over-merge unrelated networks. Edit
`stoplist.txt` to tune. Without it, one shared `sites.google.com` collapses a
dozen unrelated operations into one cluster.

## Country resolution

`actor_country` is filled from (1) the resolved named actor, else (2) the
corpus's own `country` column for that row, else (3) a country name found in the
actor string (incl. US/UK abbreviations). This keeps the impact "(unknown)"
bucket small.

## Notes

- All indicator values stay defanged in the corpus; normalization refangs only
  in memory for matching, never on disk.
- `out/` is regenerated; commit it for browsing or add to `.gitignore` to keep
  the tree clean — your call.
