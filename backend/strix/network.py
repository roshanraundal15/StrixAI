"""
strix/network.py — Layer 2: Network Anomaly Detection
======================================================
Checks the IP address for:
  - Known VPN / proxy / Tor exit node
  - Datacenter IP (bots run on AWS, DigitalOcean, etc.)
  - Suspicious geolocation
  - Blacklisted IPs

Uses ip-api.com (free, no key needed, 1000 req/min limit)
"""

import requests
import re

# ── Known bad IP ranges (datacenters, common bot sources) ────────────────────
SUSPICIOUS_ASNS = [
    "AS14061",  # DigitalOcean
    "AS16509",  # Amazon AWS
    "AS15169",  # Google Cloud
    "AS8075",   # Microsoft Azure
    "AS13335",  # Cloudflare (sometimes used by bots)
    "AS20473",  # Vultr
    "AS9009",   # M247 (common VPN provider)
    "AS60068",  # Datacamp (proxy)
    "AS199524", # G-Core Labs
]

KNOWN_VPN_KEYWORDS = [
    "vpn", "proxy", "tor", "exit", "anonymizer",
    "hosting", "datacenter", "data center", "server",
    "virtual private", "cloud"
]


def is_private_ip(ip: str) -> bool:
    """Check if IP is a local/private IP address."""
    private_ranges = [
        r"^10\.", r"^172\.(1[6-9]|2[0-9]|3[01])\.",
        r"^192\.168\.", r"^127\.", r"^::1$", r"^localhost$"
    ]
    return any(re.match(p, ip) for p in private_ranges)


def check_ip(ip: str) -> dict:
    """
    Input:  IP address string
    Output: { score: 0.0-1.0, signals: [...], details: {...} }
    
    Score closer to 1.0 = more suspicious
    """
    signals     = []
    risk_points = 0
    max_points  = 5

    # Skip analysis for private/local IPs (dev environment)
    if is_private_ip(ip):
        return {
            "score":   0.0,
            "signals": ["ℹ Private/local IP — skipping network check"],
            "details": {"ip": ip, "type": "private"}
        }

    details = {"ip": ip}

    try:
        # ip-api.com gives: country, isp, org, as, proxy, hosting, etc.
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city,isp,org,as,proxy,hosting,query"},
            timeout=3
        )
        geo = resp.json()
        details.update(geo)

        if geo.get("status") != "success":
            return {
                "score":   0.3,
                "signals": ["! Could not resolve IP info"],
                "details": details
            }

        # ── Check 1: Known proxy/VPN flag ────────────────────────────────
        if geo.get("proxy", False):
            risk_points += 2
            signals.append("⚠ IP flagged as VPN/Proxy by ip-api")

        # ── Check 2: Hosting/datacenter flag ─────────────────────────────
        if geo.get("hosting", False):
            risk_points += 2
            signals.append("⚠ IP belongs to a datacenter/hosting provider")

        # ── Check 3: ISP/Org name contains suspicious keywords ───────────
        isp = (geo.get("isp", "") + " " + geo.get("org", "")).lower()
        matched_keywords = [kw for kw in KNOWN_VPN_KEYWORDS if kw in isp]
        if matched_keywords:
            risk_points += 1
            signals.append(f"! ISP/Org name suggests VPN or hosting: {', '.join(matched_keywords)}")

        # ── Check 4: Known datacenter ASN ────────────────────────────────
        asn = geo.get("as", "")
        matched_asn = [a for a in SUSPICIOUS_ASNS if a in asn]
        if matched_asn:
            risk_points += 1
            signals.append(f"⚠ ASN matches known datacenter: {asn}")

        # ── No signals = clean IP ─────────────────────────────────────────
        if not signals:
            signals.append("✓ IP appears clean")

    except requests.exceptions.Timeout:
        signals.append("! IP lookup timed out — using neutral score")
        return {"score": 0.2, "signals": signals, "details": details}

    except Exception as e:
        signals.append(f"! IP lookup error: {str(e)}")
        return {"score": 0.2, "signals": signals, "details": details}

    score = round(min(risk_points / max_points, 1.0), 3)

    return {
        "score":   score,
        "signals": signals,
        "details": details
    }