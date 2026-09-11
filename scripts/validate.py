#!/usr/bin/env python3
"""Validate every data/**/*.csv against the corpus schema.

Checks:
  - header matches the canonical field list exactly
  - source_provider is one of the allowed providers
  - indicator_type is in the controlled vocabulary
  - actor_type / ttp_framework are in their vocabularies
  - report_date and date_added look like ISO dates (YYYY-MM-DD)
  - indicator_value is non-empty

Exit code is non-zero if any error is found, so CI can gate pull requests.
    python scripts/validate.py
"""
import csv
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import FIELDS, PROVIDERS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_vocab(name):
    path = os.path.join(ROOT, "schema", name)
    vals = set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                vals.add(r["value"].strip())
    return vals


def main():
    itypes = load_vocab("indicator_types.csv")
    atypes = load_vocab("actor_types.csv")
    frameworks = load_vocab("ttp_frameworks.csv")
    errors = []
    files = sorted(glob.glob(os.path.join(ROOT, "data", "**", "*.csv"),
                             recursive=True))
    total = 0
    for f in files:
        rel = os.path.relpath(f, ROOT)
        with open(f, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames != FIELDS:
                errors.append(f"{rel}: header mismatch\n   got:      {reader.fieldnames}\n   expected: {FIELDS}")
                continue
            for i, r in enumerate(reader, start=2):
                total += 1
                loc = f"{rel}:{i}"
                if r["source_provider"] not in PROVIDERS:
                    errors.append(f"{loc}: bad source_provider {r['source_provider']!r}")
                if itypes and r["indicator_type"] not in itypes:
                    errors.append(f"{loc}: unknown indicator_type {r['indicator_type']!r}")
                if atypes and r["actor_type"] and r["actor_type"] not in atypes:
                    errors.append(f"{loc}: unknown actor_type {r['actor_type']!r}")
                if frameworks and r["ttp_framework"] and r["ttp_framework"] not in frameworks:
                    errors.append(f"{loc}: unknown ttp_framework {r['ttp_framework']!r}")
                if not r["indicator_value"].strip():
                    errors.append(f"{loc}: empty indicator_value")
                for d in ("report_date", "date_added"):
                    if r[d] and not DATE_RE.match(r[d]):
                        errors.append(f"{loc}: {d} not ISO date: {r[d]!r}")
    if errors:
        print(f"VALIDATION FAILED: {len(errors)} problem(s) across {len(files)} files\n")
        for e in errors[:200]:
            print("  " + e)
        sys.exit(1)
    print(f"OK: {total} rows across {len(files)} files passed validation.")


if __name__ == "__main__":
    main()
