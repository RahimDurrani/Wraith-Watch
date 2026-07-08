# backend/utils/log_generator.py
# ─────────────────────────────────────────────────────────
# Background thread that generates realistic log lines
# every 1–2.5 seconds and appends them to LIVE_LOG_BUFFER.
#
# In production replace this with a real Watchdog file
# monitor or a syslog/Beats agent feeding your DB.
# ─────────────────────────────────────────────────────────

import time
import random
import threading
from datetime import datetime
from models.data import LIVE_LOG_BUFFER, LOG_LOCK, get_next_log_id

# Pool of realistic log lines — (log_type, source, hostname, message, flagged, flag_level)
LOG_POOL = [
    ("syslog", "auth.log",          "web01",        "sshd[1234]: Failed password for root from 192.168.1.10 port 22 ssh2",                             True,  "high"),
    ("syslog", "auth.log",          "web01",        "sshd[1234]: Failed password for admin from 192.168.1.10 port 22 ssh2",                            True,  "high"),
    ("syslog", "auth.log",          "web01",        "sshd[5678]: Accepted password for deploy from 10.0.0.2 port 54321 ssh2",                          False, "info"),
    ("syslog", "auth.log",          "web01",        "sshd[5678]: pam_unix(sshd:session): session opened for user deploy",                              False, "info"),
    ("syslog", "syslog",            "web01",        "sudo: alice : COMMAND=/usr/bin/apt-get install nmap",                                             True,  "medium"),
    ("syslog", "syslog",            "web01",        "kernel: Out of memory: Kill process 3241 (python3) score 901",                                    True,  "high"),
    ("syslog", "auth.log",          "web01",        "sshd[1111]: POSSIBLE BREAK-IN ATTEMPT from 203.0.113.9",                                         True,  "critical"),
    ("syslog", "syslog",            "web01",        "systemd[1]: Started Session 42 of user deploy.",                                                  False, "info"),
    ("syslog", "syslog",            "web01",        "cron[1234]: (root) CMD (/usr/lib/update-notifier/apt-daily-pamphlet)",                            False, "info"),
    ("syslog", "auth.log",          "web01",        "sshd[2222]: Invalid user testuser from 192.168.1.10 port 33456",                                 True,  "medium"),
    ("apache", "apache-access.log", "web01",        '192.168.1.10 - - "GET /admin HTTP/1.1" 403 512',                                                 True,  "medium"),
    ("apache", "apache-access.log", "web01",        '203.0.113.9 - - "GET /../etc/passwd HTTP/1.1" 400 0',                                            True,  "high"),
    ("apache", "apache-access.log", "web01",        '10.0.0.5 - - "GET /index.html HTTP/1.1" 200 2048',                                               False, "info"),
    ("apache", "apache-access.log", "web01",        '10.0.0.5 - - "POST /api/login HTTP/1.1" 200 512',                                                False, "info"),
    ("apache", "apache-access.log", "web01",        '203.0.113.9 - - "GET /wp-admin HTTP/1.1" 404 0',                                                 True,  "medium"),
    ("apache", "apache-access.log", "web01",        '172.16.0.1 - - "GET /dashboard HTTP/1.1" 200 8192',                                              False, "info"),
    ("evtx",   "Security.evtx",     "DESKTOP-WIN10","EventID 4625: An account failed to log on. TargetUser: Administrator Source: 192.168.1.10",       True,  "high"),
    ("evtx",   "Security.evtx",     "DESKTOP-WIN10","EventID 4624: An account was successfully logged on. TargetUser: deploy LogonType: 3",            False, "info"),
    ("evtx",   "Security.evtx",     "DESKTOP-WIN10","EventID 7045: A new service was installed. ServiceName: WindowsUpdateHelper",                     True,  "critical"),
    ("evtx",   "Security.evtx",     "DESKTOP-WIN10","EventID 4740: A user account was locked out. TargetUser: Administrator",                         True,  "high"),
    ("evtx",   "Security.evtx",     "DESKTOP-WIN10","EventID 4648: Logon using explicit credentials. TargetUser: Administrator",                       True,  "high"),
    ("evtx",   "System.evtx",       "FINANCE-PC",   "EventID 4624: An account was successfully logged on. TargetUser: finance_user LogonType: 2",      False, "info"),
    ("evtx",   "System.evtx",       "FINANCE-PC",   "EventID 4688: A new process was created. ProcessName: C:\\Users\\Public\\svchost32.exe",           True,  "critical"),
]


def _generate_loop():
    """Runs forever in a background daemon thread."""
    while True:
        entry = random.choice(LOG_POOL)
        log_entry = {
            "id":         get_next_log_id(),
            "timestamp":  datetime.utcnow().strftime("%H:%M:%S"),
            "log_type":   entry[0],
            "source":     entry[1],
            "hostname":   entry[2],
            "message":    entry[3],
            "flagged":    entry[4],
            "flag_level": entry[5],
        }
        with LOG_LOCK:
            LIVE_LOG_BUFFER.append(log_entry)
            if len(LIVE_LOG_BUFFER) > 200:
                LIVE_LOG_BUFFER.pop(0)
        time.sleep(random.uniform(1.0, 2.5))


def start():
    """Start the background log generator. Called once from app.py on startup."""
    t = threading.Thread(target=_generate_loop, daemon=True)
    t.start()
