#!/usr/bin/env python3
"""Normalize Meta's threat-research repo into the corpus schema.

Meta publishes two shapes of data:
  1. Classic IOC files (2020-2023):  indicator_type,indicator_value,comment,ds
  2. Online Operations Kill Chain files (2023-present):
     Tactic,Technique,Procedure,Indicator,[Comments|Notes|Note|...]

Usage:
    python scripts/normalize_meta.py /path/to/facebook-threat-research \\
        --out data/meta
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from common import FIELDS  # noqa: E402

TODAY = date.today().isoformat()
REPO = "https://github.com/facebook/threat-research/blob/main/"

# Map Meta's native classic-file type labels onto the corpus controlled vocab.
# Nuance (phishing / cib / telegram) is preserved in the description column.
TYPE_MAP = {
    "domain_name": "domain",
    "ip": "ipv4",
    "cib_url": "url",
    "phishing_url": "url",
    "telegram_url": "url",
}

# ---- indicator-type detection for the kill-chain "Indicator" column ----
RE_URL = re.compile(r"https?://|www\[?\.\]?|\bhxxp", re.I)
RE_DOMAIN = re.compile(r"^[\w\-]+(\[?\.\]?[\w\-]+)+$")
RE_IP = re.compile(r"^\d{1,3}(\[?\.\]?\d{1,3}){3}$")
RE_COUNT = re.compile(r"^\s*[\d,]+\s+[A-Za-z].*$")  # e.g. "37 Accounts"


def classify(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return "behavior"
    if RE_URL.search(v):
        return "url"
    if RE_IP.match(v):
        return "ipv4"
    if RE_DOMAIN.match(v) and " " not in v:
        return "domain"
    if RE_COUNT.match(v) and len(v) < 40:
        return "asset_count"
    return "behavior"


def country_from_name(name: str) -> str:
    m = re.search(
        r"(China|Iran|Russia|Pakistan|Poland|Belarus|Moldova|Georgia|Ukraine|"
        r"Bangladesh|Vietnam|Palestine|Togo|Burkina|Bahamut|Patchwork|Israel|"
        r"India|Serbia|Cambodia|Myanmar|Mexico|Spain|Angola|Venezuela|Cuba)",
        name, re.I)
    return m.group(1).title() if m else ""


def report_date_from_path(path: str, fname: str) -> str:
    # classic files: 2021_07_taking_action... -> 2021-07-01
    m = re.match(r"(\d{4})_(\d{2})_", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    # quarterly folders: Q1_2024 / Q2-3_2025 / Q4-1_2026
    m = re.search(r"Q([\d-]+)_(\d{4})", path)
    if m:
        q = m.group(1).split("-")[0]
        month = {"1": "01", "2": "04", "3": "07", "4": "10"}.get(q, "01")
        return f"{m.group(2)}-{month}-01"
    return ""


def actor_from_name(fname: str) -> str:
    base = os.path.splitext(os.path.basename(fname))[0]
    base = re.sub(r"^Q[\d-]+_\d{4}[ _-]*", "", base)
    base = re.sub(r"GithubIOCs\s*-\s*", "", base)
    base = base.replace("_", " ").strip()
    return base or "Meta-reported network"


def load_index(repo_root):
    idx_path = os.path.join(repo_root, "index.json")
    ref = {}
    if os.path.exists(idx_path):
        for e in json.load(open(idx_path)):
            for f in e.get("indicators", {}).get("csv_files", []):
                ref[os.path.basename(f)] = {
                    "report_date": e.get("reported_ds", ""),
                    "url": (e.get("reference_urls") or [""])[0],
                }
    return ref


def rows_for_file(path, repo_root, ref):
    fname = os.path.basename(path)
    rel = os.path.relpath(path, repo_root)
    meta = ref.get(fname, {})
    blob_url = REPO + rel.replace(" ", "%20")
    src_url = meta.get("url") or blob_url
    rdate = meta.get("report_date") or report_date_from_path(rel, fname)
    country = country_from_name(fname)
    actor = actor_from_name(fname)
    is_cib = "CIB" in fname.upper() or "network" in fname.lower()
    actor_type = "influence_operation" if is_cib else "threat_actor"

    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        header = fh.readline()
        cols = [c.strip().lower() for c in header.split(",")]
        fh.seek(0)
        reader = csv.reader(fh)
        next(reader, None)
        out = []
        classic = cols[:2] == ["indicator_type", "indicator_value"]
        for r in reader:
            if not any(c.strip() for c in r):
                continue
            if classic:
                itype = (r[0] if len(r) > 0 else "").strip()
                ival = (r[1] if len(r) > 1 else "").strip()
                comment = (r[2] if len(r) > 2 else "").strip()
                if not ival:
                    continue
                # preserve the source's finer label when we remap it to a
                # canonical type (e.g. telegram_url/phishing_url -> url)
                desc = comment
                if itype in ("cib_url", "telegram_url", "phishing_url"):
                    tag = itype.replace("_", " ")
                    desc = f"[{tag}] {comment}".strip()
                out.append({
                    "actor": actor, "actor_type": actor_type,
                    "source_provider": "meta",
                    "source_report": fname.replace(".csv", "").replace("_", " "),
                    "report_date": rdate, "source_url": src_url,
                    "indicator_type": TYPE_MAP.get(itype, itype),
                    "indicator_value": ival, "country": country,
                    "target_country": "", "target_sector": "",
                    "ttp": "", "ttp_framework": "none", "confidence": "",
                    "description": desc, "date_added": TODAY,
                })
            else:
                # kill-chain: Tactic,Technique,Procedure,Indicator,[note]
                tactic = (r[0] if len(r) > 0 else "").strip()
                tech = (r[1] if len(r) > 1 else "").strip()
                proc = (r[2] if len(r) > 2 else "").strip()
                indicator = (r[3] if len(r) > 3 else "").strip()
                note = (r[4] if len(r) > 4 else "").strip()
                if not (indicator or note or proc):
                    continue
                ttp = " > ".join(x for x in (tactic, tech, proc) if x)
                # When there is no concrete indicator, keep the row but carry
                # the procedure/behavior text as the value so it is queryable.
                if indicator:
                    itype = classify(indicator)
                    ival = indicator
                else:
                    itype = "behavior"
                    ival = proc or note or tech or tactic
                if not ival:
                    continue
                out.append({
                    "actor": actor, "actor_type": actor_type,
                    "source_provider": "meta",
                    "source_report": fname.replace(".csv", ""),
                    "report_date": rdate, "source_url": src_url,
                    "indicator_type": itype,
                    "indicator_value": ival, "country": country,
                    "target_country": "", "target_sector": "",
                    "ttp": ttp, "ttp_framework": "meta_kill_chain",
                    "confidence": "", "description": note, "date_added": TODAY,
                })
        return out, fname


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_root")
    ap.add_argument("--out", default="data/meta")
    args = ap.parse_args()
    ref = load_index(args.repo_root)
    files = sorted(glob.glob(os.path.join(args.repo_root, "indicators/csv/**/*.csv"),
                             recursive=True))
    os.makedirs(args.out, exist_ok=True)
    total = 0
    for path in files:
        rows, fname = rows_for_file(path, args.repo_root, ref)
        if not rows:
            continue
        # output filename: <report_date>_<slug>.csv
        rd = rows[0]["report_date"] or "undated"
        slug = re.sub(r"[^A-Za-z0-9]+", "-",
                      os.path.splitext(fname)[0]).strip("-").lower()[:70]
        out_path = os.path.join(args.out, f"{rd}_{slug}.csv")
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        total += len(rows)
    print(f"Meta: wrote {total} rows across {len(files)} source files -> {args.out}")


if __name__ == "__main__":
    main()
