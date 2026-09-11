# Contributing

This is a working corpus — expansions and corrections are the point. You don't
need to be a maintainer; open a PR.

## Add a new report

1. Read the report and find its indicators (Anthropic: the table at the end of
   each case study; OpenAI: throughout the operation write-ups; Meta: the repo
   or the report appendix table).
2. Create one CSV under `data/<provider>/` named `YYYY-MM-DD_slug.csv`, using
   the exact header in [`schema/fields.md`](schema/fields.md).
   - For Anthropic/OpenAI you can instead add the data to
     `scripts/backfill_anthropic_openai.py` and regenerate — that keeps the
     extraction reproducible and reviewable.
   - For a new Meta drop, re-clone `facebook/threat-research` and run
     `python3 scripts/normalize_meta.py <clone> --out data/meta`.
3. Update the report's entry in `sources.json` to `status: "ingested"` (add the
   entry if it's brand new).
4. Rebuild and validate:
   ```bash
   python3 scripts/build_master.py
   python3 scripts/validate.py     # must print OK
   ```
5. Open the PR. CI runs `validate.py` and will block on any schema violation.

## Correct an indicator

Edit the row in its `data/**/*.csv` file, rebuild, validate, PR. Note *why* in
the PR (e.g. "hash transposed during PDF extraction, fixed against source").

## Ground rules

- **Defang** every live indicator (`[.]`).
- **Cite** — every row needs a working `source_url`.
- **Don't invent** confidence, attribution, or targeting the source didn't
  state. Blank is honest.
- **Stay in vocab** — extend `schema/*.csv` in the same PR if you need a new
  type rather than overloading `description`.
- **No private/partner-shared indicators.** Only what the providers have
  published publicly belongs here.
