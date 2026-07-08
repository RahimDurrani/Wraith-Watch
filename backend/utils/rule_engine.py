# backend/utils/rule_engine.py
# ─────────────────────────────────────────────────────────
# Rule-based detection engine.
# Week 4 deliverable: 8 detection rules, severity scoring,
# alert generation from parsed log entries.
#
# How it works:
#   1. A log entry is parsed by the ingestion engine
#   2. run_rules(log_entry) checks it against all rules
#   3. Matching rules generate Alert objects saved to DB
#   4. Each alert gets an AbuseIPDB score (if IP present)
# ─────────────────────────────────────────────────────────

import re
from datetime import datetime, timedelta
from collections import defaultdict

# Track recent events per IP for threshold-based rules (brute force)
# Format: { (rule_name, source_ip): [timestamp, ...] }
_event_window: dict = defaultdict(list)


# ── Detection rules ───────────────────────────────────────────────────────────
# Each rule is a dict:
#   name        - unique identifier, shown in alert
#   description - plain-English explanation shown to analyst
#   pattern     - compiled regex matched against raw_message
#   log_types   - list of log types this rule applies to ("any" = all)
#   severity    - info | low | medium | high | critical
#   threshold   - how many matches within window_secs to fire (None = fire immediately)
#   window_secs - time window in seconds for threshold rules

RULES = [
    {
        "name":        "ssh_brute_force",
        "description": "Multiple failed SSH login attempts from the same IP within 60 seconds. "
                       "This matches the pattern of an automated brute force attack where a script "
                       "systematically tries common username/password combinations. Block the source "
                       "IP at the firewall and check whether any login attempt succeeded.",
        "pattern":     re.compile(r"Failed password|authentication failure|Invalid user", re.I),
        "log_types":   ["syslog"],
        "severity":    "critical",
        "threshold":   5,
        "window_secs": 60,
    },
    {
        "name":        "windows_service_install",
        "description": "A new Windows service was installed (Event ID 7045). Installing a new "
                       "service is a common persistence mechanism used by malware and ransomware "
                       "to survive reboots. Investigate the service name and binary path immediately.",
        "pattern":     re.compile(r"EventID 7045|new service was installed", re.I),
        "log_types":   ["evtx"],
        "severity":    "critical",
        "threshold":   None,
        "window_secs": None,
    },
    {
        "name":        "account_lockout",
        "description": "A user account was locked out (Event ID 4740). This typically occurs after "
                       "repeated failed login attempts and may indicate an active brute force attack "
                       "or a compromised account being probed. Check linked alerts from the same IP.",
        "pattern":     re.compile(r"EventID 4740|account was locked out", re.I),
        "log_types":   ["evtx"],
        "severity":    "high",
        "threshold":   None,
        "window_secs": None,
    },
    {
        "name":        "explicit_credential_logon",
        "description": "A logon was attempted using explicit credentials from a process running "
                       "as a different user (Event ID 4648). This can indicate lateral movement, "
                       "pass-the-hash attacks, or credential theft. Review the source process "
                       "and target account carefully.",
        "pattern":     re.compile(r"EventID 4648|Logon using explicit credentials", re.I),
        "log_types":   ["evtx"],
        "severity":    "high",
        "threshold":   None,
        "window_secs": None,
    },
    {
        "name":        "sudo_failure",
        "description": "A user attempted to run a privileged sudo command and failed authentication. "
                       "Repeated sudo failures may indicate an insider threat or a compromised "
                       "account attempting privilege escalation.",
        "pattern":     re.compile(r"sudo.*incorrect password|sudo.*authentication failure", re.I),
        "log_types":   ["syslog"],
        "severity":    "high",
        "threshold":   None,
        "window_secs": None,
    },
    {
        "name":        "path_traversal",
        "description": "A directory traversal sequence was detected in the HTTP request path. "
                       "Attackers use sequences like /../ or ..%2F to access files outside the "
                       "web root, targeting sensitive files like /etc/passwd or configuration files.",
        "pattern":     re.compile(r"\.\./|\.\.%2[fF]|etc/passwd|/etc/shadow|/proc/self", re.I),
        "log_types":   ["apache"],
        "severity":    "medium",
        "threshold":   None,
        "window_secs": None,
    },
    {
        "name":        "sql_injection_attempt",
        "description": "A SQL injection pattern was detected in the HTTP request. Attackers inject "
                       "SQL code into input fields to manipulate database queries, potentially "
                       "extracting sensitive data or bypassing authentication.",
        "pattern":     re.compile(
            r"union.{0,20}select|select.{0,20}from|drop.{0,10}table|"
            r"insert.{0,10}into|1=1|or\s+'1'='1|xp_cmdshell",
            re.I
        ),
        "log_types":   ["apache"],
        "severity":    "high",
        "threshold":   None,
        "window_secs": None,
    },
    {
        "name":        "breakin_attempt",
        "description": "The system detected a possible break-in attempt. This message is generated "
                       "by sshd when a remote host's DNS name does not match its IP address, which "
                       "can indicate DNS spoofing or a misconfigured attacker machine.",
        "pattern":     re.compile(r"POSSIBLE BREAK-IN ATTEMPT|BREAK-IN", re.I),
        "log_types":   ["syslog"],
        "severity":    "critical",
        "threshold":   None,
        "window_secs": None,
    },
    {
        "name":        "http_scanner",
        "description": "An automated web scanner was detected probing common vulnerable paths "
                       "such as /wp-admin, /phpmyadmin, or /.env. While often benign automated "
                       "scanning, these probes map your attack surface for potential exploitation.",
        "pattern":     re.compile(
            r"GET.*(wp-admin|phpmyadmin|\.env|\.git|xmlrpc\.php|admin\.php|config\.php)",
            re.I
        ),
        "log_types":   ["apache"],
        "severity":    "low",
        "threshold":   10,
        "window_secs": 120,
    },
    {
        "name":        "new_process_created",
        "description": "A new process was created on a Windows host (Event ID 4688). While common, "
                       "processes created from suspicious locations like Temp, Public, or AppData "
                       "can indicate malware execution.",
        "pattern":     re.compile(
            r"EventID 4688.*(?:Temp|Public|AppData|svchost32|cmd\.exe|powershell)",
            re.I
        ),
        "log_types":   ["evtx"],
        "severity":    "medium",
        "threshold":   None,
        "window_secs": None,
    },
]


def _clean_window(event_list: list, window_secs: int) -> list:
    """Remove events older than window_secs from the list."""
    cutoff = datetime.utcnow() - timedelta(seconds=window_secs)
    return [t for t in event_list if t > cutoff]


def run_rules(log_entry: dict, db, Alert) -> list:
    """
    Run all detection rules against a single log entry.

    Args:
        log_entry - dict from any parser (must have keys: raw_message, log_type, source_ip)
        db        - SQLAlchemy db instance
        Alert     - Alert model class

    Returns:
        List of Alert objects that were created and saved to DB.
    """
    raw      = log_entry.get("raw_message", "")
    log_type = log_entry.get("log_type", "")
    source_ip = log_entry.get("source_ip")
    fired    = []

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
            title          = _build_title(rule["name"], source_ip, raw),
            description    = rule["description"],
            severity       = severity,
            severity_score = Alert.score_for(severity),
            rule_name      = rule["name"],
            source_ip      = source_ip,
            log_type       = log_type,
            status         = "open",
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
        "ssh_brute_force":         f"SSH brute force{ip_suffix}",
        "windows_service_install":  "New service installed (Event 7045)",
        "account_lockout":          f"Account lockout (Event 4740){ip_suffix}",
        "explicit_credential_logon":f"Explicit credential logon (Event 4648){ip_suffix}",
        "sudo_failure":             f"Sudo failure — privilege escalation attempt{ip_suffix}",
        "path_traversal":           f"Path traversal attempt{ip_suffix}",
        "sql_injection_attempt":    f"SQL injection attempt{ip_suffix}",
        "breakin_attempt":          f"Possible break-in attempt{ip_suffix}",
        "http_scanner":             f"Web scanner detected{ip_suffix}",
        "new_process_created":      "Suspicious process created (Event 4688)",
    }
    return titles.get(rule_name, f"Alert: {rule_name}{ip_suffix}")
