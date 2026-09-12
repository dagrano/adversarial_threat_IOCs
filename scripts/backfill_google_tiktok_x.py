#!/usr/bin/env python3
"""Backfill Google (GTIG), TikTok, and X (Twitter) reporting into the schema.

Character of each source (see README scope note):
- Google GTIG: actor-by-actor AI-misuse reporting. The Jan 2025 report has no
  hard IOCs (TTP/actor rows); the Feb 2026 AI Threat Tracker adds malware
  families and some infrastructure. source_provider = google.
- TikTok: Covert Influence Operations transparency disclosures. Per-network
  detail lives in TikTok's JS transparency center (not machine-readable here),
  so this captures the aggregate + named example networks. Mark partial.
- X (Twitter): historical state-linked IO archive. Per user scope, ACCOUNT-LEVEL
  attribution only (no tweet content): one row per disclosed network with its
  attributed country and account count. source_provider = x.

Rows extracted from PDFs/blogs are machine-extracted; verify against source_url.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import FIELDS  # noqa: E402

DATE_ADDED = "2026-09-12"
rows = []


def add_actor(provider, report, rdate, url, actor, actor_type, country,
              target_country="", target_sector="", indicators=None,
              ttps=None, confidence="", note=""):
    indicators = indicators or {}
    ttps = ttps or []
    base = dict(actor=actor, actor_type=actor_type, source_provider=provider,
                source_report=report, report_date=rdate, source_url=url,
                country=country, target_country=target_country,
                target_sector=target_sector, confidence=confidence,
                date_added=DATE_ADDED)
    for itype, values in indicators.items():
        for v in values:
            r = dict.fromkeys(FIELDS, "")
            r.update(base)
            r.update(indicator_type=itype, indicator_value=v,
                     ttp="", ttp_framework="none", description=note)
            rows.append(r)
    if ttps:
        r = dict.fromkeys(FIELDS, "")
        r.update(base)
        r.update(indicator_type="ttp", indicator_value="; ".join(ttps),
                 ttp="; ".join(ttps), ttp_framework="mitre_atlas",
                 description=note or "TTP summary for this actor")
        rows.append(r)


def add_network(provider, report, rdate, url, actor, country, n_accounts,
                target="", note=""):
    """One account-level attribution row for an influence-op network."""
    r = dict.fromkeys(FIELDS, "")
    r.update(actor=actor, actor_type="influence_operation",
             source_provider=provider, source_report=report, report_date=rdate,
             source_url=url, indicator_type="asset_count",
             indicator_value=f"{n_accounts} accounts", country=country,
             target_country=target, ttp="", ttp_framework="none",
             description=note, date_added=DATE_ADDED)
    rows.append(r)


# ======================================================================
# GOOGLE — GTIG
# ======================================================================
G1 = "Adversarial Misuse of Generative AI (GTIG)"
U1 = "https://services.google.com/fh/files/misc/adversarial-misuse-generative-ai.pdf"
G2 = "GTIG AI Threat Tracker: Distillation, Experimentation, and Integration"
U2 = "https://cloud.google.com/blog/topics/threat-intelligence/distillation-experimentation-integration-ai-adversarial-use"

# ---- Jan 2025 report (no hard IOCs; actor/TTP rows) ----
add_actor("google", G1, "2025-01-29", U1, "APT42", "nation_state", "Iran",
          target_country="United States", target_sector="Defense, policy experts",
          ttps=["Phishing campaign content", "Recon on defense personnel",
                "Vuln research (Mikrotik, Apereo, Atlassian)", "Translation/localization"],
          note="~30% of Iranian APT Gemini use")
add_actor("google", G1, "2025-01-29", U1, "Iranian APT actors (10+ groups)",
          "nation_state", "Iran", target_sector="Defense, military, weapons monitoring",
          ttps=["Coding/scripting (PowerShell, Python)", "Vuln research (CVEs, WinRM, IoT)",
                "UAV/anti-drone and satellite research", "Android data-extraction research"])
add_actor("google", G1, "2025-01-29", U1, "APT41", "nation_state", "China",
          target_country="United States",
          target_sector="Military, government IT, intelligence community",
          ttps=["Recon", "Attempted extraction of Gemini system info"])
add_actor("google", G1, "2025-01-29", U1, "PRC APT actors (20+ groups)",
          "nation_state", "China", target_country="United States + 8 countries",
          target_sector="Military, IT service providers, government",
          ttps=["Windows Event Log code", "Active Directory commands",
                "EDR reverse engineering (Carbon Black)", "Lateral movement",
                "Privilege escalation", "Data exfiltration"])
add_actor("google", G1, "2025-01-29", U1, "DPRK APT actors (9 groups)",
          "nation_state", "North Korea",
          target_country="South Korea, United States, Germany; 13 countries",
          target_sector="Military, nuclear technology, defense",
          ttps=["Free-hosting infra research", "Payload development",
                "Crypto research", "Chrome infostealer conversion (Python->Node.js)",
                "IT-worker placement support", "Sandbox/VM evasion research"])
add_actor("google", G1, "2025-01-29", U1, "APT43", "nation_state", "North Korea",
          target_sector="Military, nuclear, foreign affairs",
          ttps=["North Korean nuclear-issue research", "AI image generation for personas"])
add_actor("google", G1, "2025-01-29", U1, "DPRK IT workers", "nation_state",
          "North Korea", target_country="United States",
          target_sector="Freelance gig platforms; hundreds of US companies",
          indicators={"tool": ["monica.im", "ahrefs.com", "Data Annotation Tech"]},
          ttps=["Job/salary research", "Cover-letter generation",
                "LinkedIn job research", "AI-manipulated profile photos"],
          note="Clandestine IT-worker placement scheme")
add_actor("google", G1, "2025-01-29", U1, "Russian APT actors (3 groups)",
          "nation_state", "Russia",
          ttps=["Rewriting public malware into other languages",
                "Adding AES encryption to code", "Explaining malicious code"])
add_actor("google", G1, "2025-01-29", U1, "Iranian IO actors (8 groups)",
          "influence_operation", "Iran",
          target_country="United States, Middle East, Europe",
          ttps=["~75% of all IO prompts", "SEO article generation",
                "Farsi translation", "Persona photo/logo creation",
                "Reports critical of Bahrain"])
add_actor("google", G1, "2025-01-29", U1, "DRAGONBRIDGE", "influence_operation",
          "China", target_country="United States, Taiwan",
          indicators={"social_account": ["YouTube channels (detected and terminated)"]},
          ttps=["Research on US-China relations, Taiwan, 'five poisons'",
                "AI news-presenter video (since 2022)", "Article generation"],
          note="No significant engagement gains from AI content")
add_actor("google", G1, "2025-01-29", U1, "KRYMSKYBRIDGE", "influence_operation",
          "Russia", ttps=["Research, content creation, translation"],
          note="Russian consulting firm working with the government")
add_actor("google", G1, "2025-01-29", U1, "Prigozhin-associated entities",
          "influence_operation", "Russia",
          ttps=["~40% of Russian IO activity", "Research and content creation"])
add_actor("google", G1, "2025-01-29", U1, "Doppelganger", "influence_operation",
          "Russia", ttps=["Research, content creation, translation"])
add_actor("google", G1, "2025-01-29", U1, "CopyCop", "influence_operation",
          "Russia", target_country="United States, Europe",
          ttps=["LLM-assisted article rewriting with Kremlin-aligned slant",
                "Inauthentic news sites posing as US/EU outlets"])
add_actor("google", G1, "2025-01-29", U1, "FraudGPT / WormGPT", "cybercriminal", "",
          indicators={"tool": ["FraudGPT", "WormGPT"]},
          ttps=["Uncensored LLMs advertised on Telegram", "BEC and phishing generation"])

# ---- Feb 2026 AI Threat Tracker (IOC-richer) ----
add_actor("google", G2, "2026-02-12", U2, "UNC6418", "nation_state", "",
          target_country="Ukraine", target_sector="Defense",
          ttps=["Credential/email intelligence gathering via Gemini"])
add_actor("google", G2, "2026-02-12", U2, "Temp.HEX", "nation_state", "China",
          target_country="Pakistan", target_sector="Separatist organizations",
          ttps=["Individual profiling", "Operational/structural data collection"])
add_actor("google", G2, "2026-02-12", U2, "APT42", "nation_state", "Iran",
          ttps=["Recon and social engineering", "Persona crafting",
                "Malware development acceleration"])
add_actor("google", G2, "2026-02-12", U2, "UNC2970", "nation_state", "North Korea",
          target_sector="Defense, cybersecurity companies",
          ttps=["OSINT target profiling", "High-fidelity phishing personas",
                "Job-role and salary mapping"])
add_actor("google", G2, "2026-02-12", U2, "APT31", "nation_state", "China",
          target_country="United States",
          ttps=["Automated vuln analysis via expert persona prompt",
                "RCE and WAF-bypass analysis", "SQL injection testing",
                "Abused hexstrike MCP tooling framing"])
add_actor("google", G2, "2026-02-12", U2, "UNC795", "nation_state", "China",
          ttps=["Frequent Gemini use for intrusion tooling",
                "AI-integrated code-auditing capability (agentic AI interest)"])
add_actor("google", G2, "2026-02-12", U2, "APT41", "nation_state", "China",
          ttps=["Malicious tooling development", "Code translation and troubleshooting"])
add_actor("google", G2, "2026-02-12", U2, "UNC5356", "cybercriminal", "",
          target_sector="Financial, cryptocurrency companies",
          indicators={"malware": ["COINBAIT phishing kit"],
                      "tool": ["Lovable AI", "Supabase", "Cloudflare (proxy)",
                               "Discord CDN (payloads)"]},
          ttps=["SMS/phone phishing", "React SPA credential-harvesting kit"],
          note="COINBAIT built with Lovable AI; verbose console.log fingerprints")
add_actor("google", G2, "2026-02-12", U2, "GTIG-tracked AI-enabled malware",
          "cybercriminal", "",
          indicators={"malware": ["HONESTCUE", "PROMPTFLUX", "COINBAIT", "ATOMIC",
                                  "Xanthorox"],
                      "url": ["https://www.virustotal.com/gui/collection/e72e3856e4c780078ba59c0a639b915fcab473e88f4701e16b36024d3d8c1578/summary"]},
          ttps=["Just-in-time LLM code generation (HONESTCUE/PROMPTFLUX)",
                "Fileless .NET in-memory compilation", "ClickFix distribution (ATOMIC)",
                "Gemini-backed offensive tool marketed as Xanthorox via MCP"],
          note="Malware families with AI integration; GTI VirusTotal collection linked")
add_actor("google", G2, "2026-02-12", U2, "GTIG-tracked IO actors",
          "influence_operation", "China, Iran, Russia, Saudi Arabia",
          ttps=["Political satire and propaganda generation",
                "Article, asset, and code generation via Gemini",
                "No breakthrough capabilities observed"])

# ======================================================================
# TIKTOK — Covert Influence Operations (partial; aggregate + examples)
# ======================================================================
TT = "TikTok Covert Influence Operations disclosure (Jan-Apr 2024)"
UTT = "https://newsroom.tiktok.com/en-us/strengthening-our-approach-to-countering-influence-attempts"
add_network("tiktok", TT, "2024-05-23", UTT,
            "TikTok CIO takedowns (15 operations, Jan-Apr 2024)", "", 3001,
            note="Aggregate: 15 influence operations, 3,001 accounts; majority targeted "
                 "political discourse/elections. Per-network detail is in TikTok's "
                 "transparency center (not machine-readable here) - PARTIAL, expand later.")
add_actor("tiktok", TT, "2024-05-23", UTT, "Indonesia-targeting network",
          "influence_operation", "", target_country="Indonesia",
          ttps=["Pre-2024 presidential election influence activity"])
add_actor("tiktok", TT, "2024-05-23", UTT, "UK-targeting network",
          "influence_operation", "", target_country="United Kingdom",
          ttps=["Artificial amplification of UK domestic political narratives"])

# ======================================================================
# X (Twitter) — state-linked IO archive (account-level attribution only)
# ======================================================================
X_2018 = "X/Twitter state-linked IO archive (Oct 2018 disclosure)"
UX_2018 = "https://blog.x.com/en_us/topics/company/2019/information-ops-on-twitter"
X_JUN19 = "X/Twitter state-linked IO archive (Jun 2019 disclosure)"
UX_JUN19 = UX_2018
X_SEP19 = "X/Twitter state-linked IO archive (Sep 2019 disclosure)"
UX_SEP19 = "https://blog.x.com/en_us/topics/company/2019/info-ops-disclosure-data-september-2019"
X_2020 = "X/Twitter state-linked IO archive (2020 disclosure)"
UX_2020 = "https://blog.x.com/en_us/topics/company/2020/disclosing-removed-networks-to-our-archive-of-state-linked-information"
X_2021 = "X/Twitter state-linked IO archive (Dec 2021 disclosure)"
UX_2021 = "https://blog.x.com/en_us/topics/company/2021/disclosing-state-linked-information-operations-we-ve-removed"

# 2018 (widely-cited launch figures)
add_network("x", X_2018, "2018-10-17", UX_2018, "Internet Research Agency (IRA)",
            "Russia", 3841, note="Original Oct 2018 archive; figure widely cited")
add_network("x", X_2018, "2018-10-17", UX_2018, "Iran IO network", "Iran", 770,
            note="Original Oct 2018 archive; figure widely cited")
# Jun 2019
add_network("x", X_JUN19, "2019-06-13", UX_JUN19, "Iran IO (3 sets)", "Iran", 4779,
            note="News/Israel/political personas")
add_network("x", X_JUN19, "2019-06-13", UX_JUN19, "IRA-linked accounts", "Russia", 4)
add_network("x", X_JUN19, "2019-06-13", UX_JUN19, "Catalan independence network",
            "Spain", 130, note="Catalan referendum content")
add_network("x", X_JUN19, "2019-06-13", UX_JUN19, "Venezuela commercial network",
            "Venezuela", 33, note="Commercial entity, revised attribution")
# Aug/Sep 2019
add_network("x", X_SEP19, "2019-08-19", UX_SEP19, "PRC/Hong Kong network",
            "China", 4301, target="Hong Kong protests",
            note="Most active subset of a larger 200,000+ suspended network (Aug 2019)")
add_network("x", X_SEP19, "2019-09-20", UX_SEP19, "DotDev (UAE & Egypt)",
            "United Arab Emirates", 271, note="Private tech company DotDev")
add_network("x", X_SEP19, "2019-09-20", UX_SEP19, "UAE network (Qatar/Yemen targeting)",
            "United Arab Emirates", 4248, target="Qatar, Yemen")
add_network("x", X_SEP19, "2019-09-20", UX_SEP19, "Saudi state-media accounts",
            "Saudi Arabia", 6)
add_network("x", X_SEP19, "2019-09-20", UX_SEP19, "Partido Popular network",
            "Spain", 259, note="Operated by Partido Popular")
add_network("x", X_SEP19, "2019-09-20", UX_SEP19, "PAIS Alliance network",
            "Ecuador", 1019, note="Tied to PAIS Alliance party")
# 2020
add_network("x", X_2020, "2020-06-11", UX_2020, "Iran IO network", "Iran", 104)
add_network("x", X_2020, "2020-06-11", UX_2020, "Saudi IO network", "Saudi Arabia", 33)
add_network("x", X_2020, "2020-06-11", UX_2020, "Cuba IO network", "Cuba", 526)
add_network("x", X_2020, "2020-06-11", UX_2020, "Thailand IO network", "Thailand", 926)
add_network("x", X_2020, "2020-09-01", UX_2020, "Russia IO network (5 accounts)",
            "Russia", 5)
# Dec 2021
add_network("x", X_2021, "2021-12-02", UX_2021, "Government-support network",
            "Mexico", 276, note="Civic content supporting government initiatives")
add_network("x", X_2021, "2021-12-02", UX_2021, "Uyghur-narrative network",
            "China", 2048, note="Representative sample; Uyghur narratives")
add_network("x", X_2021, "2021-12-02", UX_2021, "Changyu Culture network",
            "China", 112)
add_network("x", X_2021, "2021-12-02", UX_2021, "IRA-linked CAR operation",
            "Russia", 16, target="Central African Republic")
add_network("x", X_2021, "2021-12-02", UX_2021, "Libya/Syria operation", "Russia", 50)
add_network("x", X_2021, "2021-12-02", UX_2021, "FichuaTanzania-targeting network",
            "Tanzania", 268)
add_network("x", X_2021, "2021-12-02", UX_2021, "Pro-Museveni network", "Uganda", 418)
add_network("x", X_2021, "2021-12-02", UX_2021, "Government-narrative network",
            "Venezuela", 277)


def main():
    groups = {}
    for r in rows:
        groups.setdefault((r["source_provider"], r["report_date"],
                           r["source_report"]), []).append(r)
    for (prov, rdate, report), grp in groups.items():
        out = os.path.join("data", prov)
        os.makedirs(out, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", report.lower()).strip("-")[:55]
        with open(os.path.join(out, f"{rdate}_{slug}.csv"), "w",
                  newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(grp)
    print(f"Wrote {len(rows)} rows across {len(groups)} report files "
          f"(google + tiktok + x).")


if __name__ == "__main__":
    main()
