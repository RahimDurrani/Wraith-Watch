import time
import random
import re
import threading
from datetime import datetime

LIVE_LOG_BUFFER = []
LOG_LOCK        = threading.Lock()
_log_id_counter = 0


def get_next_log_id():
    global _log_id_counter
    _log_id_counter += 1
    return _log_id_counter

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


def _generate_loop(app):
    """
    Runs forever in a background daemon thread.

    Deliberately defensive: the whole body is wrapped per-iteration so a
    single bad tick — a DB write conflict, an import problem, anything —
    can never permanently kill this thread. If that happened, the Live
    Logs page would go blank forever with no way to recover except a
    full restart, which is exactly the failure this guards against.
    """
    import logging
    import traceback
    logger = logging.getLogger("wraithwatch.log_generator")
    confirmed_alive = False

    while True:
        try:
            entry = random.choice(LOG_POOL)
            log_type, source, hostname, message, flagged, flag_level = entry

            log_entry = {
                "id":         get_next_log_id(),
                "timestamp":  datetime.utcnow().strftime("%H:%M:%S"),
                "log_type":   log_type,
                "source":     source,
                "hostname":   hostname,
                "message":    message,
                "flagged":    flagged,
                "flag_level": flag_level,
            }
            with LOG_LOCK:
                LIVE_LOG_BUFFER.append(log_entry)
                if len(LIVE_LOG_BUFFER) > 200:
                    LIVE_LOG_BUFFER.pop(0)

            if not confirmed_alive:
                logger.info("Log generator is alive — first entry written to the live buffer.")
                confirmed_alive = True

            # ── Persist to the database so Log Search and Alerts stay real ─────
            # Best-effort: the live buffer above is what the UI depends on, so
            # a failure here must never stop the buffer from growing.
            try:
                from models.database import db, LogEntry, Alert, LogSource
                from utils.rule_engine import run_rules
                from utils.ip_reputation import enrich_alert

                with app.app_context():
                    ip_match = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", message)
                    source_ip = ip_match.group(1) if ip_match else None

                    log_row = LogEntry(
                        source_ip=source_ip, timestamp=datetime.utcnow(),
                        log_type=log_type, raw_message=message,
                        hostname=hostname, source_name=source,
                    )
                    db.session.add(log_row)
                    db.session.commit()

                    fired = run_rules(
                        {"raw_message": message, "log_type": log_type, "source_ip": source_ip},
                        db, Alert,
                    )
                    for alert in fired:
                        enrich_alert(alert, db)

                    src = LogSource.query.filter_by(name=source).first()
                    if src:
                        src.last_seen = datetime.utcnow()
                        src.total_logs += 1
                        db.session.commit()
            except Exception:
                # DB persistence failed this tick — log it once so it's visible
                # in the terminal, but keep the live buffer running regardless.
                logger.warning("log_generator: DB write failed this tick:\n%s", traceback.format_exc())

        except Exception:
            # Something broke even before the buffer append — this should be
            # essentially impossible, but log it loudly rather than dying silently.
            logger.error("log_generator: unexpected error, retrying next tick:\n%s", traceback.format_exc())

        time.sleep(random.uniform(1.0, 2.5))


def start(app):
    """Start the background log generator. Called once from app.py on startup."""
    import logging
    logging.getLogger("wraithwatch.log_generator").info(
        "Log generator starting — a new simulated log line every 1–2.5s."
    )
    t = threading.Thread(target=_generate_loop, args=(app,), daemon=True)
    t.start()

