# Schema

One row = one indicator (or one TTP summary) for one actor in one report.
All data files are UTF-8 CSV with this exact header, in this order:

| # | Field | Required | Notes |
|---|---|---|---|
| 1 | `actor` | yes | Named actor, cluster, network, or front. Use the source's name/codename (e.g. `GTG-2002`, `STORM-2035`, `China-based CIB network`). |
| 2 | `actor_type` | yes | Controlled vocab — see `actor_types.csv`. |
| 3 | `source_provider` | yes | `anthropic`, `openai`, or `meta`. |
| 4 | `source_report` | yes | Human-readable report title. |
| 5 | `report_date` | yes | ISO `YYYY-MM-DD` publication date. |
| 6 | `source_url` | yes | Direct link to the report/PDF or the source data file. |
| 7 | `indicator_type` | yes | Controlled vocab — see `indicator_types.csv`. |
| 8 | `indicator_value` | yes | The indicator itself. **Defanged** (`[.]`) as published. Never empty. |
| 9 | `country` | no | Actor origin country, if stated. |
| 10 | `target_country` | no | Targeted country/countries, if stated. |
| 11 | `target_sector` | no | Targeted sector/industry, if stated. |
| 12 | `ttp` | no | Technique reference or short description. |
| 13 | `ttp_framework` | no | Controlled vocab — see `ttp_frameworks.csv`. Use `none` for free-text. |
| 14 | `confidence` | no | As stated by the source (e.g. `high`/`medium`/`low`). Blank if the source gives none — do **not** invent one. |
| 15 | `description` | no | Free-text context / the source's own note. |
| 16 | `date_added` | yes | ISO date the row entered this corpus. |

## Conventions

- **Defanging.** Keep `[.]`, `hxxp`, `[@]` etc. as the source published them.
  If a source publishes a live indicator, defang it on entry.
- **One indicator per row.** A single actor with 30 domains produces 30 rows
  that share the actor/report/targeting columns. This keeps the file greppable
  and lets tools deduplicate on `indicator_value`.
- **TTP summary rows.** Where a report gives tradecraft but no atomic
  indicator, add one row with `indicator_type = ttp` (or `behavior`) whose
  `indicator_value` carries the technique text. This is common for OpenAI.
- **Don't fabricate.** Leave `country`, `confidence`, etc. blank when the
  source is silent. Blank is a valid, honest value.
- **Vocabulary.** If you need an `indicator_type` / `actor_type` /
  `ttp_framework` that doesn't exist, add it to the relevant `schema/*.csv` in
  the same PR so `validate.py` accepts it — don't stuff it into `description`.
