

import re
from datetime import datetime, timedelta
from collections import defaultdict

_event_window: dict = defaultdict(list)


RULES = [
    {
        "name": "ssh_brute_force",
        "description": "5+ failed SSH logins from one IP inside 60s — looks like an automated "
                       "credential-stuffing/brute-force run. Block the IP and check for a "
                       "successful login mixed in with the failures.",
        "pattern": re.compile(r"Failed password|authentication failure|Invalid user", re.I),
        "log_types": ["syslog"],
        "severity": "critical",
        "threshold": 5,
        "window_secs": 60,
    },
    {
        "name": "windows_service_install",
        "description": "New Windows service installed (Event ID 7045) — a classic persistence "
                       "trick. Check the service name and binary path.",
        "pattern": re.compile(r"EventID 7045|new service was installed", re.I),
        "log_types": ["evtx"],
        "severity": "critical",
        "threshold": None,
        "window_secs": None,
    },
    {
        "name": "account_lockout",
        "description": "Account lockout (Event ID 4740) — usually the tail end of a brute-force "
                       "run. Cross-check other alerts from the same source IP.",
        "pattern": re.compile(r"EventID 4740|account was locked out", re.I),
        "log_types": ["evtx"],
        "severity": "high",
        "threshold": None,
        "window_secs": None,
    },
    {
        "name": "explicit_credential_logon",
        "description": "Explicit-credential logon (Event ID 4648) — a process ran using different "
                       "credentials than the logged-on user. Worth a look for lateral movement or "
                       "pass-the-hash activity.",
        "pattern": re.compile(r"EventID 4648|Logon using explicit credentials", re.I),
        "log_types": ["evtx"],
        "severity": "high",
        "threshold": None,
        "window_secs": None,
    },
    {
        "name": "sudo_failure",
        "description": "Failed sudo authentication. Could just be a typo, but repeated failures "
                       "on the same account are worth watching for privilege escalation.",
        "pattern": re.compile(r"sudo.*incorrect password|sudo.*authentication failure", re.I),
        "log_types": ["syslog"],
        "severity": "high",
        "threshold": None,
        "window_secs": None,
    },
    {
        "name": "path_traversal",
        "description": "Path traversal sequence (../ or similar) in the request path — an attempt "
                       "to reach files outside the web root.",
        "pattern": re.compile(r"\.\./|\.\.%2[fF]|etc/passwd|/etc/shadow|/proc/self", re.I),
        "log_types": ["apache"],
        "severity": "medium",
        "threshold": None,
        "window_secs": None,
    },
    {
        "name": "sql_injection_attempt",
        "description": "SQL injection pattern in the request — someone's trying to slip query "
                       "syntax into an input field.",
        "pattern": re.compile(
            r"union.{0,20}select|select.{0,20}from|drop.{0,10}table|"
            r"insert.{0,10}into|1=1|or\s+'1'='1|xp_cmdshell",
            re.I
        ),
        "log_types": ["apache"],
        "severity": "high",
        "threshold": None,
        "window_secs": None,
    },
    {
        "name": "breakin_attempt",
        "description": "sshd flagged a possible break-in attempt — the remote host's reverse DNS "
                       "didn't match its IP. Could be DNS spoofing, could just be a misconfigured box.",
        "pattern": re.compile(r"POSSIBLE BREAK-IN ATTEMPT|BREAK-IN", re.I),
        "log_types": ["syslog"],
        "severity": "critical",
        "threshold": None,
        "window_secs": None,
    },
    {
        "name": "http_scanner",
        "description": "10+ requests hitting common scanner targets (/wp-admin, /phpmyadmin, "
                       "/.env, etc.) within 2 minutes. Usually mass-scanning bots rather than a "
                       "targeted attack, but it's mapping your attack surface either way.",
        "pattern": re.compile(
            r"GET.*(wp-admin|phpmyadmin|\.env|\.git|xmlrpc\.php|admin\.php|config\.php)",
            re.I
        ),
        "log_types": ["apache"],
        "severity": "low",
        "threshold": 10,
        "window_secs": 120,
    },
    {
        "name": "new_process_created",
        "description": "New process spawned from Temp/Public/AppData, or a cmd/PowerShell child "
                       "process (Event ID 4688). Common false-positive rate, but it's the kind of "
                       "spot malware likes to run from.",
        "pattern": re.compile(
            r"EventID 4688.*(?:Temp|Public|AppData|svchost32|cmd\.exe|powershell)",
            re.I
        ),
        "log_types": ["evtx"],
        "severity": "medium",
        "threshold": None,
        "window_secs": None,
    },
]


def _clean_window(event_list: list, window_secs: int) -> list:
    """Remove events older than window_secs from the list."""
    cutoff = datetime.utcnow() - timedelta(seconds=window_secs)
    return [t for t in event_list if t > cutoff]


def run_rules(log_entry: dict, db, Alert) -> list:
    """Run all detection rules against a log entry, saving and returning any alerts fired."""
    raw = log_entry.get("raw_message", "")
    log_type = log_entry.get("log_type", "")
    source_ip = log_entry.get("source_ip")
    fired = []

    for rule in RULES:
        # Check log type compatibility
        if rule["log_types"] != ["any"] and log_type not in rule["log_types"]:
            continue

        # Check if pattern matches
        if not rule["pattern"].search(raw):
            continue

        # Handle threshold-based rules
        if rule["threshold"] and rule["window_secs"] and source_ip:
            key = (rule["name"], source_ip)
            _event_window[key] = _clean_window(_event_window[key], rule["window_secs"])
            _event_window[key].append(datetime.utcnow())

            if len(_event_window[key]) < rule["threshold"]:
                continue  # Not enough events yet — don't fire

            # Reset counter after firing
            _event_window[key] = []

        # Create alert
        severity = rule["severity"]
        alert = Alert(
            title = _build_title(rule["name"], source_ip, raw),
            description = rule["description"],
            severity = severity,
            severity_score = Alert.score_for(severity),
            rule_name = rule["name"],
            source_ip = source_ip,
            log_type = log_type,
            status = "open",
        )
        db.session.add(alert)
        fired.append(alert)

    if fired:
        db.session.commit()

    return fired


def _build_title(rule_name: str, source_ip: str | None, raw: str) -> str:
    """Build a human-readable alert title from rule name and context."""
    ip_suffix = f" — {source_ip}" if source_ip else ""
    titles = {
        "ssh_brute_force": f"SSH brute force{ip_suffix}",
        "windows_service_install": "New service installed (Event 7045)",
        "account_lockout": f"Account lockout (Event 4740){ip_suffix}",
        "explicit_credential_logon":f"Explicit credential logon (Event 4648){ip_suffix}",
        "sudo_failure": f"Sudo failure — privilege escalation attempt{ip_suffix}",
        "path_traversal": f"Path traversal attempt{ip_suffix}",
        "sql_injection_attempt": f"SQL injection attempt{ip_suffix}",
        "breakin_attempt": f"Possible break-in attempt{ip_suffix}",
        "http_scanner": f"Web scanner detected{ip_suffix}",
        "new_process_created": "Suspicious process created (Event 4688)",
    }
    return titles.get(rule_name, f"Alert: {rule_name}{ip_suffix}")
