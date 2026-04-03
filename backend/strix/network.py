"""
strix/network.py — Layer 2: Network Anomaly Detection
Checks IP for VPN/proxy/datacenter with caching to avoid timeouts.
"""

import requests
import re

SUSPICIOUS_ASNS = [
    "AS14061","AS16509","AS15169","AS8075","AS13335",
    "AS20473","AS9009","AS60068","AS199524",
]
KNOWN_VPN_KEYWORDS = [
    "vpn","proxy","tor","exit","anonymizer",
    "hosting","datacenter","data center","server",
    "virtual private","cloud"
]

# Simple in-memory cache so the same IP isn't looked up twice
_ip_cache = {}

def is_private_ip(ip: str) -> bool:
    private_ranges = [
        r"^10\.", r"^172\.(1[6-9]|2[0-9]|3[01])\.",
        r"^192\.168\.", r"^127\.", r"^::1$", r"^localhost$"
    ]
    return any(re.match(p, ip) for p in private_ranges)

def check_ip(ip: str) -> dict:
    signals     = []
    risk_points = 0
    max_points  = 5

    if is_private_ip(ip):
        return {
            "score":   0.0,
            "signals": ["Private/local IP — skipping network check"],
            "details": {"ip": ip, "type": "private"}
        }

    # Return cached result if available
    if ip in _ip_cache:
        return _ip_cache[ip]

    details = {"ip": ip}

    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city,isp,org,as,proxy,hosting,query"},
            timeout=2   # reduced from 3 to 2 seconds
        )
        geo = resp.json()
        details.update(geo)

        if geo.get("status") != "success":
            return {"score": 0.3, "signals": ["Could not resolve IP info"], "details": details}

        if geo.get("proxy", False):
            risk_points += 2
            signals.append("IP flagged as VPN/Proxy")

        if geo.get("hosting", False):
            risk_points += 2
            signals.append("IP belongs to datacenter/hosting")

        isp = (geo.get("isp","") + " " + geo.get("org","")).lower()
        if any(kw in isp for kw in KNOWN_VPN_KEYWORDS):
            risk_points += 1
            signals.append(f"ISP/Org suggests VPN or hosting")

        asn = geo.get("as","")
        if any(a in asn for a in SUSPICIOUS_ASNS):
            risk_points += 1
            signals.append(f"ASN matches known datacenter: {asn}")

        if not signals:
            signals.append("IP appears clean")

    except Exception:
        # On timeout or error, give a neutral score and move on fast
        result = {"score": 0.1, "signals": ["IP lookup skipped (timeout)"], "details": details}
        _ip_cache[ip] = result
        return result

    score  = round(min(risk_points / max_points, 1.0), 3)
    result = {"score": score, "signals": signals, "details": details}

    # Cache the result
    _ip_cache[ip] = result
    return result