import os
import requests
from datetime import datetime, timedelta
_cache: dict = {}
CACHE_TTL_MINUTES = 60


def _is_private_ip(ip: str) -> bool:
    """
    Skip AbuseIPDB checks for private/internal IPs — they won't be in the database.
    Covers RFC1918 ranges: 10.x, 172.16-31.x, 192.168.x
    """
    if not ip:
        return True
    parts = ip.split(".")
    if len(parts) != 4:
        return True
    try:
        a, b = int(parts[0]), int(parts[1])
        return (
            a == 10
            or a == 127
            or (a == 172 and 16 <= b <= 31)
            or (a == 192 and b == 168)
        )
    except ValueError:
        return True


def check_ip(ip: str) -> dict | None:
    """
    Look up an IP address on AbuseIPDB.

    Returns a dict with score and country, or None if:
    - The IP is private/internal
    - No API key is configured
    - The API call fails

    Args:
        ip - IPv4 address string

    Returns:
        {
            "abuse_score": 87,        # 0-100 confidence of abuse
            "abuse_country": "RU",      # ISO country code
        }
        or None
    """
    if not ip or _is_private_ip(ip):
        return None

    api_key = os.environ.get("ABUSEIPDB_API_KEY", "").strip()
    if not api_key:
        # No API key configured — return None silently
        # The frontend handles None gracefully (shows "—")
        return None

    # Check cache first
    if ip in _cache:
        cached = _cache[ip]
        age = datetime.utcnow() - cached["checked_at"]
        if age < timedelta(minutes=CACHE_TTL_MINUTES):
            return {
                "abuse_score": cached["score"],
                "abuse_country": cached["country"],
            }

    try:
        response = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={
                "Key": api_key,
                "Accept": "application/json",
            },
            params={
                "ipAddress": ip,
                "maxAgeInDays": 90,
                "verbose": "",
            },
            timeout=5,
        )
        if response.status_code != 200:
            return None

        data = response.json().get("data", {})
        score = data.get("abuseConfidenceScore", 0)
        country = data.get("countryCode", "")

        # Cache the result
        _cache[ip] = {
            "score": score,
            "country": country,
            "checked_at": datetime.utcnow(),
        }

        return {"abuse_score": score, "abuse_country": country}

    except (requests.RequestException, ValueError, KeyError):
        return None


def enrich_alert(alert, db) -> None:
    """
    Look up the alert's source IP and update the alert with AbuseIPDB data.
    Called after an alert is created by the rule engine.

    Args:
        alert - Alert model instance
        db    - SQLAlchemy db instance
    """
    if alert.abuse_checked or not alert.source_ip:
        return

    result = check_ip(alert.source_ip)
    if result:
        alert.abuse_score = result["abuse_score"]
        alert.abuse_country = result["abuse_country"]

    alert.abuse_checked = True
    db.session.commit()
