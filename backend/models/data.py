# backend/models/data.py
# ─────────────────────────────────────────────────────────
# In-memory seed data — alerts, incidents, log sources,
# users, live log buffer, upload history.
#
# In your real project replace these with SQLAlchemy models
# and a PostgreSQL database (Week 9 of your roadmap).
# ─────────────────────────────────────────────────────────

import threading
from datetime import datetime

# ── Alerts ────────────────────────────────────────────────────────────────────
ALERTS = [
    {"id":1,"title":"SSH brute force — 18 attempts / 60s","severity":"critical","severity_score":5,"source_ip":"192.168.1.10","rule":"ssh_brute_force","log_type":"syslog","status":"open","abuse_score":87,"abuse_country":"RU","created_at":"2026-06-04T09:23:01","description":"18 failed SSH login attempts were detected from 192.168.1.10 within 60 seconds. This matches an automated brute force attack. The IP has an AbuseIPDB score of 87 — a known malicious host. Block this IP at the firewall immediately and check whether any login attempt succeeded."},
    {"id":2,"title":"New service installed (Event 7045)","severity":"critical","severity_score":5,"source_ip":"10.10.10.44","rule":"service_install","log_type":"evtx","status":"open","abuse_score":62,"abuse_country":"CN","created_at":"2026-06-04T09:15:00","description":"A new Windows service was installed on DESKTOP-WIN10. Event ID 7045 is a common persistence mechanism used by malware and ransomware to survive reboots. Investigate the service name and binary path immediately."},
    {"id":3,"title":"Account lockout — Administrator (Event 4740)","severity":"high","severity_score":4,"source_ip":"192.168.1.10","rule":"account_lockout","log_type":"evtx","status":"in_progress","abuse_score":87,"abuse_country":"RU","created_at":"2026-06-04T09:08:00","description":"The Administrator account was locked out after repeated failed login attempts. This is likely a continuation of the brute force attack from 192.168.1.10."},
    {"id":4,"title":"Explicit credential logon (Event 4648)","severity":"high","severity_score":4,"source_ip":"172.16.0.5","rule":"explicit_cred","log_type":"evtx","status":"open","abuse_score":12,"abuse_country":"GB","created_at":"2026-06-04T09:01:00","description":"A logon was attempted using explicit credentials from a process running as a different user. This can indicate lateral movement or credential theft."},
    {"id":5,"title":"Sudo failure — root escalation attempt","severity":"high","severity_score":4,"source_ip":"10.0.0.8","rule":"sudo_fail","log_type":"syslog","status":"open","abuse_score":5,"abuse_country":"GB","created_at":"2026-06-04T08:55:00","description":"A user attempted to run a privileged sudo command and failed authentication. Repeated sudo failures may indicate privilege escalation."},
    {"id":6,"title":"Path traversal attempt — /../etc/passwd","severity":"medium","severity_score":3,"source_ip":"203.0.113.9","rule":"path_traversal","log_type":"apache","status":"false_positive","abuse_score":95,"abuse_country":"NL","created_at":"2026-06-04T08:49:00","description":"A directory traversal sequence was detected in the HTTP request path targeting /etc/passwd. AbuseIPDB score 95 — likely an automated scanner."},
    {"id":7,"title":"Failed logins ×6 — invalid user","severity":"medium","severity_score":3,"source_ip":"192.168.1.10","rule":"failed_login","log_type":"syslog","status":"open","abuse_score":87,"abuse_country":"RU","created_at":"2026-06-04T08:41:00","description":"Six failed SSH login attempts for non-existent usernames were recorded. Username enumeration often precedes a targeted brute force attack."},
    {"id":8,"title":"Off-hours login — 03:14 UTC","severity":"low","severity_score":2,"source_ip":"10.0.0.22","rule":"offhours_login","log_type":"syslog","status":"open","abuse_score":3,"abuse_country":"GB","created_at":"2026-06-04T03:14:00","description":"A successful login occurred at 03:14 UTC, outside normal working hours. Verify with the user."},
    {"id":9,"title":"HTTP 403 flood — /admin (×42)","severity":"low","severity_score":2,"source_ip":"203.0.113.9","rule":"http_flood","log_type":"apache","status":"closed","abuse_score":95,"abuse_country":"NL","created_at":"2026-06-04T07:30:00","description":"42 HTTP 403 responses were returned probing /admin. Likely an automated web scanner. The endpoint is properly protected."},
]

# ── Incidents ─────────────────────────────────────────────────────────────────
INCIDENTS = [
    {"id":1,"title":"Brute force cluster — web01","severity":"critical","status":"investigating","analyst":"Alice","alert_ids":[1,3,7],"created_at":"2026-06-04T09:25:00","updated_at":"2026-06-04T09:40:00","description":"Multiple alerts linked to 192.168.1.10 indicate an active brute force campaign against web01.","notes":[{"author":"Alice","content":"IP blocked at firewall. Checking auth logs for any successful logins.","created_at":"2026-06-04T09:35:00"},{"author":"Alice","content":"No successful logins confirmed. Monitoring for further attempts from different IPs.","created_at":"2026-06-04T09:42:00"}],"audit":[{"action":"Incident created","user":"Alice","time":"09:25"},{"action":"Status: new → triaged","user":"Alice","time":"09:28"},{"action":"Status: triaged → investigating","user":"Alice","time":"09:33"}]},
    {"id":2,"title":"Suspicious service installation","severity":"high","status":"triaged","analyst":"Bob","alert_ids":[2],"created_at":"2026-06-04T09:20:00","updated_at":"2026-06-04T09:30:00","description":"A new Windows service was installed on DESKTOP-WIN10. Potentially a persistence mechanism.","notes":[{"author":"Bob","content":"Service name: WindowsUpdateHelper. Binary path: C:\\Users\\Public\\svchost32.exe — highly suspicious.","created_at":"2026-06-04T09:28:00"}],"audit":[{"action":"Incident created","user":"Bob","time":"09:20"},{"action":"Status: new → triaged","user":"Bob","time":"09:26"}]},
    {"id":3,"title":"Account lockout — Finance PC","severity":"high","status":"new","analyst":None,"alert_ids":[3,4],"created_at":"2026-06-04T09:10:00","updated_at":"2026-06-04T09:10:00","description":"Administrator account lockout on Finance PC. Needs assignment.","notes":[],"audit":[{"action":"Incident created","user":"System","time":"09:10"}]},
]

# ── Log sources ───────────────────────────────────────────────────────────────
LOG_SOURCES = [
    {"id":1,"name":"apache-access.log","type":"apache","hostname":"web01","last_seen":"2026-06-04T09:44:48","status":"active","total_logs":4821,"minutes_ago":0},
    {"id":2,"name":"auth.log","type":"syslog","hostname":"web01","last_seen":"2026-06-04T09:44:15","status":"active","total_logs":2341,"minutes_ago":1},
    {"id":3,"name":"Security.evtx","type":"evtx","hostname":"DESKTOP-WIN10","last_seen":"2026-06-04T09:37:00","status":"stale","total_logs":892,"minutes_ago":8},
    {"id":4,"name":"syslog","type":"syslog","hostname":"web01","last_seen":"2026-06-04T09:43:00","status":"active","total_logs":1203,"minutes_ago":2},
    {"id":5,"name":"System.evtx","type":"evtx","hostname":"FINANCE-PC","last_seen":"2026-06-04T07:00:00","status":"silent","total_logs":341,"minutes_ago":105},
]

CHART_DATA = [2, 4, 3, 6, 2, 8, 5, 4, 9, 12, 7, 14]

# ── Upload history ────────────────────────────────────────────────────────────
UPLOAD_HISTORY = []   # appended to as files are uploaded

# ── Users store ───────────────────────────────────────────────────────────────
# Swap for a SQLAlchemy User model when you move to PostgreSQL
USERS         = []
_next_user_id = 1


def get_next_user_id():
    global _next_user_id
    uid = _next_user_id
    _next_user_id += 1
    return uid


# ── Live log buffer ───────────────────────────────────────────────────────────
LIVE_LOG_BUFFER = []   # rolling buffer of last 200 generated log lines
LOG_LOCK        = threading.Lock()
LOG_ID_COUNTER  = 1


def get_next_log_id():
    global LOG_ID_COUNTER
    lid = LOG_ID_COUNTER
    LOG_ID_COUNTER += 1
    return lid
