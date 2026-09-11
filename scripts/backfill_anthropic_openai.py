#!/usr/bin/env python3
"""Backfill Anthropic and OpenAI report indicators into the corpus schema.

Indicators here are extracted from the published report PDFs. Anthropic
publishes IOC tables per case study; OpenAI publishes very few hard technical
indicators (they state they share those privately with industry partners), so
OpenAI rows are largely actor/operation-level: origin, targeting, and TTPs.

IMPORTANT: rows sourced from PDFs are machine-extracted and should be
spot-checked against the source_url before operational use. Each row carries
its source_url so verification is one click away.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import FIELDS  # noqa: E402

OUT_A = "data/anthropic"
OUT_O = "data/openai"
DATE_ADDED = "2026-09-11"

rows = []


def add_actor(provider, report, rdate, url, actor, actor_type, country,
              target_country="", target_sector="",
              indicators=None, ttps=None, confidence="", persona=None,
              note=""):
    """Emit one row per indicator, plus one summary TTP/behavior row."""
    indicators = indicators or {}
    ttps = ttps or []
    persona = persona or []
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
    for p in persona:
        r = dict.fromkeys(FIELDS, "")
        r.update(base)
        r.update(indicator_type="persona", indicator_value=p,
                 ttp="", ttp_framework="none", description=note)
        rows.append(r)
    # one row capturing the TTP set (framework = mitre_atlas for AI-abuse TTPs)
    if ttps:
        r = dict.fromkeys(FIELDS, "")
        r.update(base)
        r.update(indicator_type="ttp", indicator_value="; ".join(ttps),
                 ttp="; ".join(ttps), ttp_framework="mitre_atlas",
                 description=note or "TTP summary for this actor/operation")
        rows.append(r)


# ======================================================================
# ANTHROPIC
# ======================================================================
A_MAR25 = "Detecting and Countering Malicious Uses of Claude: March 2025"
U_MAR25 = "https://cdn.sanity.io/files/4zrzovbb/website/45bc6adf039848841ed9e47051fb1209d6bb2b26.pdf"
A_AUG25 = "Detecting and countering misuse of AI: August 2025"
U_AUG25 = "https://www-cdn.anthropic.com/b2a76c6f6992465c09a6f2fce282f6c0cea8c200.pdf"
A_SEP26 = "Detecting and countering misuse of AI: September 2026"
U_SEP26 = "https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf"

# ---- March 2025 (IOC-sparse; case studies without disclosed hard IOCs) ----
add_actor("anthropic", A_MAR25, "2025-03-01", U_MAR25,
          "Multi-client influence network", "influence_operation", "",
          ttps=["100+ social media bot accounts across X/Facebook",
                "Persona engagement-decision orchestration",
                "Multilingual content generation",
                "Image-generation prompt creation/evaluation"],
          note="Case study 1; no hard IOCs disclosed")
add_actor("anthropic", A_MAR25, "2025-03-01", U_MAR25,
          "IoT credential scraping actor", "cybercriminal", "",
          target_sector="Internet-facing security cameras",
          ttps=["Leaked-credential database integration",
                "Stealer-log community monitoring",
                "Open-source toolkit modification"],
          note="Case study 2; no hard IOCs disclosed")
add_actor("anthropic", A_MAR25, "2025-03-01", U_MAR25,
          "Recruitment fraud actor", "fraud", "",
          target_country="Eastern Europe",
          ttps=["Real-time language sanitization of comms",
                "Impersonation of legitimate hiring managers"],
          note="Case study 3; no hard IOCs disclosed")
add_actor("anthropic", A_MAR25, "2025-03-01", U_MAR25,
          "Novice malware developer", "cybercriminal", "",
          ttps=["Facial recognition tool development",
                "Dark web scanning", "Evasion-focused payload generation"],
          note="Case study 4; no hard IOCs disclosed")

# ---- August 2025 ----
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "GTG-2002", "cybercriminal", "",
          target_sector="Healthcare, emergency services, government, religious; 17+ orgs",
          ttps=["Claude Code for recon, credential harvesting, network penetration",
                "Chisel tunneling", "Active Directory / Kerberos attacks",
                "AI-driven ransom-note generation and ransom pricing"],
          note="'Vibe hacking' data-extortion operation")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "DPRK IT worker fraud", "nation_state", "North Korea",
          target_country="United States",
          target_sector="Fortune 500 technology companies",
          persona=["Isabella Martinez (example persona)"],
          ttps=["False identity creation", "Passing technical assessments",
                "Maintaining fraudulent remote employment"],
          note="North Korean employment fraud")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "GTG-5004", "cybercriminal", "United Kingdom",
          indicators={
              "onion_domain": ["techscckl72ibnfg2ksj5aqlanwgzw32asr6ml37aojnyw4nardojyid[.]onion"],
              "email": ["techscriptservices@proton[.]me"],
          },
          ttps=["Ransomware-as-a-service ($400-$1,200)",
                "ChaCha20/AES-256 encryption",
                "FreshyCalls/RecycledGate syscall evasion",
                "Reflective DLL injection", "Shadow-copy deletion",
                "Sold on Dread, CryptBB, Nulled"],
          note="No-code ransomware RaaS")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "Chinese APT (Vietnam infrastructure)", "nation_state", "China",
          target_country="Vietnam",
          target_sector="Telecommunications, government databases, agriculture",
          ttps=["9-month campaign spanning 12/14 ATT&CK tactics",
                "Custom Python scanning", "WordPress exploitation",
                "Linux kernel privilege escalation",
                "Hydra/hashcat credential access", "Proxy-chain evasion"],
          note="Chinese APT targeting Vietnamese critical infrastructure")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "Contagious Interview (Famous Chollima / UNC5342 / DEV#POPPER)",
          "nation_state", "North Korea",
          target_sector="Software developers (global); 140+ victims (external)",
          ttps=["Fake technical interviews via LinkedIn/GitHub",
                "Malicious npm packages", "ClickFix technique"],
          indicators={"malware": ["BeaverTail", "InvisibleFerret",
                                   "OtterCookie", "GolangGhost"]},
          note="DPRK malware distribution; auto-disrupted")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "Russian-speaking malware developer", "cybercriminal", "Russia",
          target_country="Russia, United Kingdom, Ukraine",
          ttps=["Hell's Gate syscall resolution", "Early Bird injection",
                "Telegram bot C2", "App masquerading (Zoom, crypto tools)",
                "Samples on VirusTotal within 2h of generation"],
          note="Russian-speaking malware developer")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "MCP stealer-log analysis actor", "cybercriminal", "Russia",
          indicators={"forum": ["xss[.]is"]},
          ttps=["MCP-based stealer-log analysis and victim profiling"],
          note="Stealer-log analysis via MCP")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "AI-powered carding store", "cybercriminal", "",
          target_sector="Financial / stolen credit cards",
          ttps=["Multi-API card-validation framework with failover",
                "Automated card checking, request throttling"],
          note="Spanish-speaking operator")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "Romance-scam bot operator", "fraud", "China",
          target_country="United States, Japan, Korea",
          indicators={"telegram": ["@Chat_ChatGPT_AIbot"]},
          ttps=["High-EI romance-scam response generation",
                "10,000+ monthly users", "Profile image generation"],
          note="Telegram romance-scam bot; primarily Chinese-language channels")
add_actor("anthropic", A_AUG25, "2025-08-27", U_AUG25,
          "Synthetic identity services", "fraud", "",
          ttps=["Fraudulent synthetic-identity creation and services"],
          note="Case study 10; no hard IOCs disclosed")

# ---- September 2026 (IOC-rich) ----
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-20006", "nation_state", "Russia",
          target_country="Ukraine, Europe, Middle East, Asia",
          target_sector="Government, defense, intelligence, diplomacy, think tanks",
          indicators={
              "domain": ["ms365-live[.]com", "teams.ms365-live[.]com",
                         "m365-owa[.]com", "owa-ms365[.]com", "ms365-device[.]com",
                         "mslivetest.duckdns[.]org", "my-invite[.]org",
                         "chamber-ua[.]org", "chathamhouse[.]eu",
                         "ukrinform-share[.]net", "ad-g[.]org", "docs-viewer[.]org",
                         "wa-connect[.]eu", "mygreatmarket[.]org", "mygreatmarket[.]com",
                         "cdncounter[.]net", "static.cdncounter[.]net",
                         "stuseamandesilt[.]org", "api.stuseamandesilt[.]org",
                         "cdn.stuseamandesilt[.]org", "update.stuseamandesilt[.]org",
                         "itechx[.]tel", "pdfviewer2024.b-cdn[.]net",
                         "meridian-protocol[.]org", "meridiangroup-corp[.]com",
                         "projectnightcrawler[.]dev", "metricwave[.]org",
                         "mgsend[.]org", "wa-meeting[.]com", "russianearabroad[.]com",
                         "russianearabroad[.]org", "embassy-protocol[.]int"],
              "ipv4": ["104.145.210[.]184", "31.57.243[.]154", "104.194.151[.]133",
                       "104.194.159[.]55", "144.172.114[.]192", "213.145.86[.]112",
                       "2.26.53[.]194", "148.135.195[.]111", "185.198.234[.]26",
                       "185.198.234[.]101", "149.54.42[.]106", "104.194.149[.]228",
                       "38.146.28[.]132", "38.146.28[.]75"],
              "email": ["anna.manager@russianearabroad[.]net",
                        "events@embassy-protocol[.]int"],
              "sha256": ["be99857449d2856dd5a84e21c8a3d5e0e01456adb44062ddec5a6b4970d8d42c",
                         "918fa52ae45ed60ba7cc8bdc99c3cbe9ab92e0375ec31fc05d0d4513be11c593"],
              "filename": ["msedgeupdate_v3.exe", "msedgeupdate.exe", "version.dll",
                           "WUEngine.exe", "DiagHost.exe",
                           "client_20260507093021_4286d211_x64.exe", "fix_network.apk"],
              "malware": ["PowerChrome", "WUEngine", "Shadow C2", "MiniPlasma",
                          "CloudSyncSvc", "GiftDrop", "DarkSword"],
          },
          ttps=["Device-code phishing", "DNS hijacking", "WhatsApp account takeover",
                "Cloud email espionage ('Embassy Kit')", "Fake-update social engineering"],
          note="Russian espionage")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-50014 (ShinyHunters; aliases MeowSHA, frkoo, blazespider)",
          "cybercriminal", "France",
          target_sector="SaaS, technology, retail, energy, airlines, nonprofits",
          indicators={
              "domain": ["policenationale[.]cc", "autoshop.policenationale[.]cc",
                         "soraki[.]cc", "soraki[.]work", "emailsecure[.]email",
                         "mozilla[.]ws", "signin-1psswoord[.]com", "on-pssword[.]com",
                         "ari-chain[.]com", "arichain[.]network", "bitmart-mystery[.]com",
                         "defi-claim[.]xyz", "service-infos[.]info",
                         "updatebeacon.duckdns[.]org",
                         "esvfecawvjmchjslqyemho2fiduc59wzn.oast[.]fun",
                         "soraki-proxy.20245aad98d27b1b1a2f0f103e1d7ee0.workers[.]dev"],
              "ipv4": ["162.128.129[.]106", "195.178.110[.]131", "45.148.10[.]242",
                       "92.118.39[.]3", "185.65.134[.]246", "185.65.134[.]199",
                       "193.32.249[.]161", "193.32.249[.]164", "193.32.249[.]170",
                       "104.36.50[.]54", "104.193.135[.]207", "91.171.138[.]169",
                       "176.177.12[.]62"],
              "ipv6": ["2a04:cec0:1185:34f2:a150:7081:caed:448e",
                       "2a01:e0a:2e2:aa40:b15d:5d28:6f4a:8d53"],
              "url": ["https://s3.eu-central-1.s4.mega[.]io/fuckyoubasil/",
                      "0x0[.]st"],
              "telegram": ["-1003893854338 (ClintonHog)", "-1003311614569 (ChatMignon)",
                           "bot:8632748474", "bot:8664033117", "bot:8628746407",
                           "bot:8709258476", "user:8179098353"],
          },
          ttps=["APK decompilation & secret scanning", "GitHub API key harvesting",
                "Supply-chain compromise", "XSS exploitation",
                "Session-token theft", "Cross-tenant data exfiltration", "Vibe hacking"],
          note="ShinyHunters opportunistic attacks")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-10007", "nation_state", "China",
          target_country="Middle East, Europe, Southeast Asia",
          target_sector="Education, retail, energy, tech, healthcare, finance, gov",
          ttps=["Autonomous vulnerability research", "Binary reverse engineering",
                "Zero-day exploit development", "Agent-swarm exploitation",
                "Targeted 50 organizations globally"],
          note="Chinese exploit foundry (Changsha, Hunan)")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-50021 (alias kl1zy)", "cybercriminal", "Russia/Ukraine",
          indicators={
              "domain": ["awstore[.]cloud", "kiro[.]cheap", "sys-tools[.]cfd",
                         "aws-us-east-3[.]com", "holdboost[.]store", "deltaclient[.]xyz",
                         "iymkjuzymkapovrntoxy.supabase[.]co"],
          },
          ttps=["Credential harvesting", "Fraudulent AI reseller networks",
                "Proxy-service interception"],
          note="Fraudulent AI reseller operation")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-50020", "cybercriminal", "Russia",
          target_sector="AI vendors (formerly hotel booking, fintech)",
          indicators={
              "ipv4": ["141.133.125[.]208", "167.250.111[.]136", "178.16.54[.]141",
                       "37.27.103[.]22", "194.163.183[.]216", "202.66.167[.]230",
                       "146.103.101[.]253", "146.103.97[.]169"],
          },
          ttps=["Prompt injection on LiteLLM", "Eval-sandbox compromise",
                "Production API-key theft", "Malicious instruction injection"],
          note="Russian financial crime pivoting to AI supply chain")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-50029", "hacktivist", "France",
          target_country="Europe",
          target_sector="Political parties, media, think tanks, SaaS",
          indicators={
              "domain": ["prod-artfkt[.]com", "fafwatch[.]xyz",
                         "frntrs-analytics.dedyn[.]io",
                         "frntrs-analytics-863060591218.europe-west1.run[.]app"],
              "onion_domain": ["3ell6n47y3ct4a3x67fbuz62q2mk2l4vo6eacho2suzftdshsnrfopyd[.]onion",
                               "6mshbvhvzhdgumwwazf4jcep2xx4kdk6n4wgffc46msu2gc3j3t2fpad[.]onion"],
              "ipv4": ["139.59.2[.]243", "158.173.46[.]118", "146.70.116[.]131",
                       "149.22.83[.]6", "138.199.60[.]29", "138.199.6[.]208",
                       "103.216.220[.]19", "103.124.165[.]199", "103.141.60[.]144",
                       "34.156.199[.]132", "34.156.95[.]176", "136.144.242[.]56",
                       "163.172.157[.]53"],
              "ipv6": ["2001:ac8:27:89::a02d", "2001:ac8:29:84::a01d",
                       "2001:bc8:711:5854:dc00:1ff:fe18:ba53"],
          },
          ttps=["WordPress race-condition exploitation", "Webshell in font assets",
                "MU-plugin credential harvesting", "Backup poisoning",
                "Browser-exploitation C2"],
          note="French hacktivist campaign")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-04001", "influence_operation", "Russia",
          target_country="Central African Republic",
          indicators={"radio": ["Radio Lengo Songo 98.9 FM"],
                       "telegram": ["СОМБ (Туристы в Африке)", "Залечь на дне в Банги"]},
          ttps=["State-media coordination (RT, Sputnik Afrique, TASS)",
                "Content laundering", "Forged government documents",
                "Opposition surveillance"],
          note="Russian CAR influence op (Politology / Africa Corps, assessed SVR-controlled)")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-54002 (LKM Company)", "influence_operation", "France",
          target_country="US, Brazil, France, DR Congo",
          indicators={
              "domain": ["naijapulse[.]org", "axumvoices[.]org", "jambojournal[.]org",
                         "zion-pulse[.]com", "alwatanalakbar[.]com", "echoberlin[.]info",
                         "british-daily[.]com", "russianway[.]info", "pakssarzameen[.]org",
                         "voiceoftherejuvenation[.]com", "elpulsopopular[.]com",
                         "fiftystates[.]news", "civicpulse[.]info", "commonwealth-post[.]com"],
              "social_account": ["@Naijapulse_", "@AxumVoices", "@journaljambo",
                                  "@zionpulse", "@saudinews966", "@berlin_echo",
                                  "@britishdaily_", "@RussianWayMedia", "@PSarzameeninfo",
                                  "@fuxingmedia", "@elpulsopopular", "@Fiftystatesnews",
                                  "@Civicpulsemedia", "@cmwthpost"],
          },
          ttps=["Commercial influence-as-a-service", "250+ X accounts, 70+ fake outlets"],
          note="Commercial influence-as-a-service (LKM, France)")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-84005 (BBS Bilisim Teknolojileri)", "influence_operation", "Turkey",
          target_country="Malaysia",
          indicators={
              "domain": ["malaysiapulse[.]com", "bbsteknoloji[.]com"],
              "ipv4": ["23.88.118[.]216", "91.99.117[.]166", "157.180.93[.]7",
                       "167.235.157[.]100", "46.62.214[.]3", "46.225.91[.]180"],
              "github": ["github[.]com/bbsbilisimteknolojileri-cell"],
              "social_account": ["@armsam1209", "@kioskou", "@Chikmore", "@avihoue",
                                 "@goldsteve1", "@adriansantodo", "@bmmyangels",
                                 "@telkisoszoba", "@SHIHAN1947", "@garyponce",
                                 "@hugolaurent", "@exceiivier", "@malaysiapulseof"],
          },
          ttps=["~1,000 fake X accounts", "222 parliamentary constituencies targeted"],
          note="Malaysian election manipulation platform")
add_actor("anthropic", A_SEP26, "2026-09-10", U_SEP26,
          "GTG-24015", "influence_operation", "Russia",
          target_country="Moldova, Latin America, Africa",
          indicators={
              "domain": ["eadaily[.]com", "point[.]md", "vz[.]ru", "mos[.]news",
                         "ru[.]euronews[.]com"],
              "telegram": ["@rybar_america", "@boris_rozhin", "@theaterVD",
                           "@china3army", "@kalashnikovnews", "@ATodaPotencia"],
          },
          ttps=["State-media editorial pipelines (Sputnik, RIA, RT)",
                "Source laundering", "Moldova election interference (2025-09-28)"],
          note="Russian state-media editorial pipelines")

# ======================================================================
# OPENAI  (operation-level; few hard IOCs by design)
# ======================================================================
O_JUN25 = "Disrupting malicious uses of AI: June 2025"
U_JUN25 = "https://cdn.openai.com/threat-intelligence-reports/5f73af09-a3a3-4a55-992e-069237681620/disrupting-malicious-uses-of-ai-june-2025.pdf"
O_OCT25 = "Disrupting malicious uses of AI: October 2025"
U_OCT25 = "https://cdn.openai.com/threat-intelligence-reports/7d662b68-952f-4dfd-a2f2-fe55b041cc4a/disrupting-malicious-uses-of-ai-october-2025.pdf"

# ---- June 2025 ----
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "DPRK IT worker scheme", "nation_state", "North Korea",
          target_sector="Global IT / software engineering (remote roles)",
          ttps=["AI resume fabrication", "Coding-assignment automation",
                "Geolocation masking (Tailscale, OBS, vdo.ninja, HDMI loops)"],
          note="Deceptive employment scheme")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "Sneer Review", "influence_operation", "China",
          target_country="Taiwan, Pakistan, United States",
          indicators={"social_account": ["Multiple TikTok/X/Facebook (handles not disclosed)"]},
          ttps=["Bulk comments (English, Chinese, Urdu)",
                "Main-then-reply false engagement",
                "Targeted 'Reversed Front' game; defamation of Mahrang Baloch"],
          note="Claimed CCP Propaganda Dept affiliation (unverified)")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "High Five (Comm&Sense Inc)", "influence_operation", "Philippines",
          target_country="Philippines",
          ttps=["Five TikTok channels, identical videos",
                "Bulk short comments via low-follower accounts",
                "'Princess Fiona' nickname for VP Duterte"],
          note="Domestic political influence op")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "VAGue Focus (VAG Group front)", "influence_operation", "China",
          target_country="United States, Europe",
          indicators={"social_account": ["Focus Lens News", "BrightWave Media Europe",
                                          "Visionary Advisory Group (nine X accounts)"]},
          ttps=["Covert persona creation", "Correspondence translation to US Senator",
                "Intelligence-collection cover via fake campaigns"],
          note="Turkey-based front; active in mainland China business hours")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "Helgoland Bite", "influence_operation", "Russia",
          target_country="Germany",
          indicators={"domain": ["Pravda DE (Portal Kombat network)"],
                       "telegram": ["Nachhall von Helgoland (1,755 subs)"],
                       "social_account": ["X account 27,000+ followers, AI profile image"]},
          ttps=["German-language election content", "AfD support / NATO criticism",
                "Reposting to Pravda network"],
          note="2025 German election interference")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "ScopeCreep", "cybercriminal", "Russia",
          target_sector="Windows / gaming overlay users",
          indicators={"malware": ["Trojanized 'Crosshair-X' gaming tool",
                                   "Go-based multi-stage malware", "python310.dll"],
                       "telegram": ["Attacker-controlled C2 channel"]},
          ttps=["DLL side-loading via pythonw.exe", "Themida packing",
                "Defender exclusion via PowerShell", "SOCKS5 obfuscation",
                "Browser credential/cookie theft"],
          note="Russian-speaking actor")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "Vixen Panda (APT15) / Keyhole Panda (APT5)", "nation_state", "China",
          target_country="United States",
          target_sector="Federal defense, military, government technology",
          ttps=["reNgine web recon", "Selenium auth-token capture",
                "Local LLM (DeepSeek) deployment", "Nmap-output analysis for pentest",
                "Android fleet management for social automation",
                "SIPRNET/JWICS research", "Exploit payload generation"],
          note="PRC-linked cyber operations")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "Uncle Spam", "influence_operation", "China",
          target_country="United States",
          indicators={"social_account": ["X and Bluesky accounts posing as US veterans",
                                          "'Veterans for Justice' logos"]},
          ttps=["Tariff-polarization content (both sides)",
                "Data scraping (Tweepy, Nitter, Bluesky API)",
                "AI-generated profile images"],
          note="US political polarization")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "STORM-2035", "influence_operation", "Iran",
          target_country="US, UK, Ireland, Venezuela, Cuba, Palestine, Iran",
          indicators={"social_account": ["X accounts posing as US/UK/Ireland/Venezuela residents"]},
          ttps=["Persian prompts generating English/Spanish tweets",
                "Following >> followers pattern", "Category 1 (negligible engagement)"],
          note="Recidivist Iranian influence activity")
add_actor("openai", O_JUN25, "2025-06-05", U_JUN25,
          "Wrong Number", "fraud", "Cambodia",
          target_country="Global (EN, ES, Swahili, Kinyarwanda, DE, Haitian Creole)",
          indicators={"persona": ["Hyesung Advertising", "Lightning Shared Scooter Co (LSSC)"]},
          ttps=["Task-scam cold SMS", "WhatsApp->Telegram 'mentor' routing (BonChat)",
                "'Ping/Zing/Sting' workflow", "Crypto deposit extraction"],
          note="Task-scam / pig-butchering operation")

# ---- October 2025 ----
add_actor("openai", O_OCT25, "2025-10-07", U_OCT25,
          "Russian-language malware tooling developer", "cybercriminal", "Russia",
          ttps=["LLM-optimized payload crafting", "Anomaly-detection evasion",
                "Post-compromise assistance", "Infrastructure profiling",
                "Models refused direct exploit/keylogger requests"],
          note="Credential theft, RATs, UAC/SmartScreen bypass")
add_actor("openai", O_OCT25, "2025-10-07", U_OCT25,
          "Korean-language operators (likely DPRK, unconfirmed)", "nation_state",
          "North Korea", target_country="South Korea",
          target_sector="Diplomatic missions",
          indicators={"malware": ["XenoRAT"], "github": ["GitHub-based C2 repositories"]},
          ttps=["Chrome->Safari extension conversion", "DPAPI browser credential workflows",
                "reCAPTCHA clone development"],
          note="Related to Trellix reporting; attribution not independently confirmed")
add_actor("openai", O_OCT25, "2025-10-07", U_OCT25,
          "UTA0388 / UNK_DROPPITCH", "nation_state", "China",
          target_country="Taiwan, United States",
          target_sector="Semiconductors, academia, think tanks, CCP critics",
          indicators={"malware": ["GOVERSHELL (Volexity)", "HealthKick (Proofpoint)"],
                       "tool": ["nuclei", "fscan"]},
          ttps=["ChatGPT-registration emails correlated with phishing",
                "WebSocket C2 with AES-GCM (static key)",
                "Edge/WebView2 process targeting"],
          note="PRC phishing and scripting operation")
add_actor("openai", O_OCT25, "2025-10-07", U_OCT25,
          "Cambodia / Myanmar / Nigeria scam networks", "fraud",
          "Cambodia, Myanmar, Nigeria",
          target_country="United States, Latin America",
          ttps=["Fake investment sites", "Cold SMS -> WhatsApp groups",
                "Em-dash removal to evade AI-text detection"],
          note="ChatGPT used to spot scams 3x more than to run them (per OpenAI)")
add_actor("openai", O_OCT25, "2025-10-07", U_OCT25,
          "PRC government-linked authoritarian tooling", "nation_state", "China",
          target_sector="Uyghur, ethnic/religious/political monitoring",
          ttps=["Social media 'probe' (探针) for extremist/ethnic/political speech",
                "'High-risk Uyghur inflow warning model' (transport vs police records)",
                "Anti-CCP account funding analysis"],
          note="Cannot independently verify government use (per OpenAI)")
add_actor("openai", O_OCT25, "2025-10-07", U_OCT25,
          "Stop News", "influence_operation", "Russia",
          target_country="Africa, United Kingdom",
          indicators={"domain": ["newstop[.]africa"],
                       "social_account": ["Newstop Africa (X, 172 followers)",
                                          "YouTube/TikTok newsreader channels"]},
          ttps=["AI-generated newsreader video", "News-outlet impersonation",
                "Pro-Russia / anti-France narratives"],
          note="Recidivist; Breakout Scale Category 2")
add_actor("openai", O_OCT25, "2025-10-07", U_OCT25,
          "Nine-emdash Line", "influence_operation", "China",
          target_country="South China Sea, Vietnam, Philippines, Hong Kong, US",
          indicators={"social_account": ["X / Instagram / TikTok accounts (many suspended)"],
                       "persona": ["Targeted HK activists: Jimmy Lai, Nathan Law, Agnes Chow"]},
          ttps=["Bulk posts (Cantonese, English)", "Tibetan-name generation for accounts",
                "#MyImmigrantStory TikTok strategy", "Self-reply coordination"],
          note="Compared to Spamouflage; Breakout Scale Category 2")


def main():
    os.makedirs(OUT_A, exist_ok=True)
    os.makedirs(OUT_O, exist_ok=True)
    # group by (provider, report_date, report) -> file
    groups = {}
    for r in rows:
        key = (r["source_provider"], r["report_date"], r["source_report"])
        groups.setdefault(key, []).append(r)
    import re
    for (prov, rdate, report), grp in groups.items():
        out = OUT_A if prov == "anthropic" else OUT_O
        slug = re.sub(r"[^a-z0-9]+", "-", report.lower()).strip("-")[:50]
        path = os.path.join(out, f"{rdate}_{slug}.csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(grp)
    print(f"Wrote {len(rows)} rows across {len(groups)} report files "
          f"(anthropic + openai).")


if __name__ == "__main__":
    main()
