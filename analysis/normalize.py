#!/usr/bin/env python3
"""Indicator normalization — the shared substrate for overlap and linked-ops.

The same indicator appears in many shapes across reports: `evil[.]com` vs
`evil.com`, `http://evil.com/x` vs the bare host, `www.` prefixes, mixed case,
IPs with `[.]`. `canonicalize()` collapses those to a single comparable key so
two rows that mean the same thing actually match.

It returns a match "class" and "key". Two indicators are the same iff they share
(class, key). Classes deliberately join related types — a URL's host, a bare
domain, and an email's domain all land in the `netloc` class — so a domain in a
Meta file can match a URL host in an Anthropic report.

stdlib only.
"""
import re

# indicator_type -> match class. Types in the same class are comparable.
CLASS = {
    "domain": "netloc", "url": "netloc", "email": "netloc", "onion_domain": "netloc",
    "ipv4": "ip", "ipv6": "ip",
    "sha256": "hash", "sha1": "hash", "md5": "hash",
    "telegram": "handle", "social_account": "handle", "github": "handle",
    "android_package_name": "package", "ios_app_id": "package",
    "crypto_wallet": "wallet",
    "malware": "malware", "tool": "tool",
    "forum": "netloc", "radio": "other",
    "asset_count": "metric", "behavior": "text", "ttp": "text",
    "filename": "filename", "persona": "persona",
}

_SCHEME = re.compile(r"^[a-z][a-z0-9+.\-]*://", re.I)


def refang(s: str) -> str:
    """Undo common defanging so values compare equal to their live form."""
    if not s:
        return ""
    s = s.strip()
    s = s.replace("[.]", ".").replace("(.)", ".").replace("{.}", ".")
    s = s.replace("[.", ".").replace(".]", ".")
    s = s.replace("[at]", "@").replace("(at)", "@").replace("[@]", "@")
    s = re.sub(r"^h(?:xx|tt|XX)p", "http", s, flags=re.I)
    s = s.replace("[:]", ":").replace("[/]", "/")
    return s


def _host_of(value: str) -> str:
    v = _SCHEME.sub("", value)          # drop scheme
    v = v.split("/", 1)[0]              # drop path
    v = v.split("?", 1)[0].split("#", 1)[0]
    v = v.rsplit("@", 1)[-1]           # drop userinfo / email local part
    v = v.split(":", 1)[0]             # drop port
    if v.startswith("www."):
        v = v[4:]
    return v.strip(".").lower()


def canonicalize(indicator_type: str, value: str) -> dict:
    """Return {class, key, host, raw} for one indicator.

    `key` is the value to match on; `host` is the registrable host where one
    applies (netloc types), useful for grouping subdomains later.
    """
    itype = (indicator_type or "").strip().lower()
    raw = value or ""
    cls = CLASS.get(itype, "other")
    v = refang(raw)
    host = ""

    if cls == "netloc":
        host = _host_of(v)
        key = host
    elif cls == "ip":
        key = _host_of(v) if "/" not in v else v.strip().lower()
        key = key.strip("[]")
    elif cls == "hash":
        key = re.sub(r"[^0-9a-f]", "", v.lower())
    elif cls == "handle":
        key = v.lstrip("@").strip().lower()
    elif cls == "package":
        key = v.strip().lower()
    elif cls in ("malware", "tool"):
        key = re.sub(r"\s+", " ", v.strip().lower())
    elif cls == "wallet":
        key = v.strip()  # wallets are case-sensitive; keep as-is
    else:
        # metric / text / persona / filename / other: normalize whitespace/case
        key = re.sub(r"\s+", " ", v.strip().lower())

    return {"class": cls, "key": key, "host": host, "raw": raw}


# ---- metric parsing (seeds the network-impact analysis) ----
_METRIC = re.compile(r"^\s*([\d,]+)\s+(.*?)\s*$")
_UNIT_MAP = {
    "account": "accounts", "accounts": "accounts",
    "facebook account": "accounts", "facebook accounts": "accounts",
    "instagram account": "accounts", "instagram accounts": "accounts",
    "x/twitter account": "accounts", "twitter account": "accounts",
    "page": "pages", "pages": "pages",
    "group": "groups", "groups": "groups",
    "channel": "channels", "channels": "channels",
    "follower": "followers", "followers": "followers",
}


def parse_metric(value: str):
    """'117 Facebook accounts' -> (117, 'accounts'). None if not a count."""
    m = _METRIC.match(refang(value or ""))
    if not m:
        return None
    try:
        n = int(m.group(1).replace(",", ""))
    except ValueError:
        return None
    unit_raw = m.group(2).strip().lower()
    unit = _UNIT_MAP.get(unit_raw)
    if not unit:
        for k, v in _UNIT_MAP.items():
            if k in unit_raw:
                unit = v
                break
    return n, (unit or unit_raw or "items")


if __name__ == "__main__":  # tiny self-test
    for t, v in [("domain", "MS365-live[.]com"), ("url", "https://www.Evil.com/x?a=1"),
                 ("email", "bob@evil[.]com"), ("ipv4", "1.2.3[.]4"),
                 ("social_account", "@Naija_"), ("asset_count", "117 Facebook accounts")]:
        print(f"{t:16} {v!r:34} -> {canonicalize(t, v)}")
    print("metric:", parse_metric("117 Facebook accounts"))
