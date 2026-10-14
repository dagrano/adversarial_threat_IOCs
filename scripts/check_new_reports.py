#!/usr/bin/env python3
"""Monthly check for new / un-ingested threat reports.

Two things it does, using only the standard library:

  1. Meta: pulls the live file tree of facebook/threat-research from the
     GitHub API and reports any indicators/csv/*.csv files that have no
     matching normalized file under data/meta/. New ones can be pulled in by
     re-running scripts/normalize_meta.py against a fresh clone.

  2. Anthropic / OpenAI: prints any report in sources.json still marked
     "pending", and fetches each provider listing page so a human (or the
     scheduled Claude task) can eyeball newly published editions that are not
     yet in sources.json.

    python scripts/check_new_reports.py

Exit code is 0 always; this is an advisory report, not a gate.
"""
import glob
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "ai-threat-indicators-checker/1.0"}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def check_meta():
    print("\n=== META (facebook/threat-research) ===")
    api = ("https://api.github.com/repos/facebook/threat-research/"
           "git/trees/main?recursive=1")
    try:
        tree = json.loads(fetch(api))["tree"]
    except Exception as e:  # noqa: BLE001
        print(f"  could not reach GitHub API: {e}")
        return
    remote = [n["path"] for n in tree
              if n["path"].startswith("indicators/csv/") and n["path"].endswith(".csv")]
    # normalized meta files are named <date>_<slug>.csv; match loosely by slug
    local = glob.glob(os.path.join(ROOT, "data", "meta", "*.csv"))
    local_slugs = set()
    for f in local:
        base = os.path.basename(f)
        base = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", base)
        local_slugs.add(re.sub(r"[^a-z0-9]", "", base.lower()))
    new = []
    for p in remote:
        slug = re.sub(r"[^a-z0-9]", "", os.path.splitext(os.path.basename(p))[0].lower())
        # normalized slug is truncated to 70 chars; compare on a prefix
        if not any(slug[:40] in ls or ls[:40] in slug for ls in local_slugs):
            new.append(p)
    print(f"  remote CSV files: {len(remote)}, local normalized: {len(local)}")
    if new:
        print(f"  {len(new)} source file(s) not yet normalized:")
        for p in new:
            print("    +", p)
        print("  -> re-clone the repo and run scripts/normalize_meta.py")
    else:
        print("  up to date.")


def check_meta_atr(meta):
    """Meta narrative Adversarial Threat Reports (data/meta-reports/ vein).

    These are hand-curated per-network rows, NOT the facebook/threat-research
    IOC CSVs. Meta now publishes ~twice-annually, so this prints the latest
    ingested edition and scans the transparency listing for newer links so a
    human (or the scheduled task) can ingest any new networks as a new
    data/meta-reports/<date>_<slug>.csv.
    """
    print("\n=== META ATR (narrative reports, data/meta-reports/) ===")
    atr = meta.get("atr_reports", [])
    if not atr:
        print("  no atr_reports tracked in sources.json.")
        return
    latest = max(r["date"] for r in atr)
    print(f"  {len(atr)} editions ingested; latest = {latest} "
          f"(cadence: {meta.get('atr_cadence', 'unknown')})")
    known = {r["url"] for r in atr}
    lu = meta.get("atr_listing_url")
    if not lu:
        return
    try:
        html = fetch(lu)
    except Exception as e:  # noqa: BLE001
        print(f"  (could not fetch listing {lu}: {e})")
        return
    links = set(re.findall(r'href="([^"]+)"', html))
    cand = [l for l in links if re.search(r"(adversarial|threat-report|/sr/)", l, re.I)]
    fresh = sorted({l for l in cand if l.startswith("http") and l not in known})
    if fresh:
        print("  candidate ATR links not in sources.json atr_reports:")
        for c in fresh[:25]:
            print("    ?", c)
        print("  -> if an edition is newer than the latest above, extract its "
              "networks into data/meta-reports/ (see sources.json atr_note).")
    else:
        print("  no new ATR links detected on the listing page.")


def check_lab(name, data):
    print(f"\n=== {name.upper()} ===")
    pending = [r for r in data["reports"] if r.get("status") == "pending"]
    if pending:
        print(f"  {len(pending)} report(s) marked pending in sources.json:")
        for r in pending:
            print(f"    - {r['date']}  {r['title']}\n      {r['url']}")
    else:
        print("  no reports marked pending.")
    known = {r["url"] for r in data["reports"]}
    for lu in data.get("listing_urls", []):
        try:
            html = fetch(lu)
        except Exception as e:  # noqa: BLE001
            print(f"  (could not fetch listing {lu}: {e})")
            continue
        links = set(re.findall(r'href="([^"]+)"', html))
        cand = [l for l in links
                if re.search(r"(malicious|misuse|threat|influence|disrupt)", l, re.I)]
        fresh = [c for c in cand if c not in known and c.startswith("http")]
        if fresh:
            print(f"  candidate links on {lu} not in sources.json:")
            for c in sorted(set(fresh))[:25]:
                print("    ?", c)


def main():
    with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as fh:
        src = json.load(fh)["providers"]
    check_meta()
    check_meta_atr(src.get("meta", {}))
    # every provider except meta (which has its own GitHub-tree + ATR checks)
    for name, data in src.items():
        if name == "meta":
            continue
        check_lab(name, data)
    print("\nDone. Ingest anything new, update sources.json status, "
          "then run build_master.py + validate.py.")


if __name__ == "__main__":
    main()
    sys.exit(0)
