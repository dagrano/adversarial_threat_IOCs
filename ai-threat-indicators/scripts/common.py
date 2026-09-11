"""Shared definitions for the AI-provider threat-indicator corpus."""

# Canonical column order for every data/**/*.csv file and the master build.
FIELDS = [
    "actor",            # named actor / cluster / network (e.g. GTG-2002, "China-based CIB network")
    "actor_type",       # see schema/actor_types.csv
    "source_provider",  # anthropic | openai | meta
    "source_report",    # human-readable report title
    "report_date",      # ISO 8601 (YYYY-MM-DD) publication date
    "source_url",       # direct link to the report/PDF or the source data file
    "indicator_type",   # see schema/indicator_types.csv
    "indicator_value",  # the indicator itself (defanged where applicable)
    "country",          # actor origin country, if stated
    "target_country",   # targeted country/countries, if stated
    "target_sector",    # targeted sector/industry, if stated
    "ttp",              # technique reference or description
    "ttp_framework",    # mitre_attack | mitre_atlas | meta_kill_chain | none
    "confidence",       # as stated by the source (e.g. high/medium/low), else blank
    "description",      # free-text note / context
    "date_added",       # ISO date this row was added to the corpus
]

def load_providers():
    """Allowed source_provider values, from schema/providers.csv if present.

    Kept as data (not a hardcoded set) so new sources — google, tiktok, OSINT,
    security-vendor reporting — can be added by editing one CSV, no code change.
    """
    import csv
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "schema", "providers.csv")
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            return {r["value"].strip() for r in csv.DictReader(fh) if r["value"].strip()}
    return {"anthropic", "openai", "meta"}


PROVIDERS = load_providers()
