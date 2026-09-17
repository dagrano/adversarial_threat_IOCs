#!/usr/bin/env python3
"""Actor resolution — collapse messy per-report actor strings to canonical IDs.

Two problems this solves:
  1. Named actors appear under different names across providers (Meta's
     "Spamouflage ..." == Google's "DRAGONBRIDGE"; APT41 == Winnti). A curated
     alias map (aliases.csv) maps every known alias to one canonical_id.
  2. Meta's actor strings are filename-derived and noisy ("CHINA BASED CIB
     NETWORK", "Iran-based CIB network 1"). These are per-report network labels,
     not named actors — we normalize casing and pull out the origin country, but
     keep them distinct (is_named = False) so overlap logic can weight a shared
     *named* actor as strong evidence and a shared generic label as weak.

resolve(actor_string) -> dict(canonical_id, canonical_name, country, is_named).
stdlib only.
"""
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

COUNTRIES = ["China", "Iran", "Russia", "North Korea", "DPRK", "Pakistan",
             "Vietnam", "Bangladesh", "Turkey", "Türkiye", "Poland", "Belarus",
             "Moldova", "Georgia", "Ukraine", "Israel", "India", "Serbia",
             "Cambodia", "Myanmar", "Mexico", "Spain", "Angola", "Venezuela",
             "Cuba", "Thailand", "Saudi Arabia", "Tanzania", "Uganda", "Ecuador",
             "United Arab Emirates", "UAE", "Egypt", "France", "Croatia",
             "Lebanon", "Ghana", "Benin", "Romania", "Bahrain", "Togo",
             "Burkina Faso", "Palestine", "Syria", "Honduras", "Indonesia",
             "United Kingdom", "United States"]
_CANON_COUNTRY = {"dprk": "North Korea", "uae": "United Arab Emirates",
                  "türkiye": "Turkey"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def load_aliases(path=None):
    path = path or os.path.join(HERE, "aliases.csv")
    amap = {}          # normalized alias -> row
    meta = {}          # canonical_id -> (name, country)
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            amap[_norm(r["alias"])] = r
            meta.setdefault(r["canonical_id"], (r["canonical_name"], r["country"]))
    # longest aliases first so "vixen panda" wins over "apt15" substrings etc.
    order = sorted(amap, key=len, reverse=True)
    return amap, meta, order


_ALIASES, _META, _ORDER = load_aliases()


def _country_in(s: str) -> str:
    low = _norm(s)
    for c in COUNTRIES:
        if re.search(r"\b" + re.escape(c.lower()) + r"\b", low):
            return _CANON_COUNTRY.get(c.lower(), c)
    return ""


def resolve(actor_string: str) -> dict:
    s = actor_string or ""
    low = _norm(s)
    # 1) named-actor alias match (whole-word, longest alias first)
    for alias in _ORDER:
        if re.search(r"\b" + re.escape(alias) + r"\b", low):
            row = _ALIASES[alias]
            return {"canonical_id": row["canonical_id"],
                    "canonical_name": row["canonical_name"],
                    "country": row["country"] or _country_in(s),
                    "is_named": True,
                    "match_confidence": row.get("confidence", "")}
    # 2) generic per-report network label: normalize + tag country
    country = _country_in(s)
    # strip filename cruft / quarter tags for a cleaner label
    label = re.sub(r"\b(q[1-4](-\d)?|h[12]|cs\d|20\d\d|#\d|\d)\b", " ", low)
    label = re.sub(r"\b(taking action against hackers in|removing coordinated "
                   r"inauthentic behavior from|githubiocs)\b", " ", label)
    label = re.sub(r"\s+", " ", label).strip(" -")
    if not label:
        label = low
    cid = "LABEL:" + re.sub(r"[^a-z0-9]+", "-", label).strip("-")[:48]
    name = label.title() if label else s
    return {"canonical_id": cid, "canonical_name": name, "country": country,
            "is_named": False, "match_confidence": ""}


if __name__ == "__main__":
    for a in ["Doppelganger Russia based CIB network updated",
              "DRAGONBRIDGE", "Spamouflage China based CIB updated",
              "APT41", "Vixen Panda (APT15) / Keyhole Panda (APT5)",
              "IRAN-BASED CIB NETWORK", "Contagious Interview (Famous Chollima "
              "/ UNC5342 / DEV#POPPER)", "RUSSIA-BASED CIB NETWORK #2"]:
        r = resolve(a)
        print(f"{a[:52]:54} -> {r['canonical_id']:26} named={r['is_named']} "
              f"country={r['country']}")
