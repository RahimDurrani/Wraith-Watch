# backend/utils/seeder.py
# ─────────────────────────────────────────────────────────
# Seeds the database with demo data on first run.
# Only runs if the relevant tables are empty.
# Replaces the old hardcoded lists in models/data.py.
# ─────────────────────────────────────────────────────────

import logging
from datetime import datetime, timedelta

logger = logging.getLogger("wraithwatch.seeder")


def seed_all(app, bcrypt):
    """Run all seeders. Call once from app.py after db.create_all()."""
    with app.app_context():
        from models.database import db, User, Alert, Incident, IncidentNote, \
            IncidentAudit, LogSource

        _seed_users(db, User, bcrypt)
        _seed_alerts(db, Alert)
        _seed_incidents(db, Incident, IncidentNote, IncidentAudit, Alert)


def _seed_users(db, User, bcrypt):
    if User.query.count() > 0:
        return

    users = [
        User(username="analyst",
             email="analyst@soc.local",
             password_hash=bcrypt.generate_password_hash("Password123!").decode("utf-8"),
             role="admin"),
        User(username="alice",
             email="alice@soc.local",
             password_hash=bcrypt.generate_password_hash("Password123!").decode("utf-8"),
             role="analyst"),
        User(username="bob",
             email="bob@soc.local",
             password_hash=bcrypt.generate_password_hash("Password123!").decode("utf-8"),
             role="analyst"),
    ]
    db.session.add_all(users)
    db.session.commit()
    logger.info(f"Seeded {len(users)} users.")


def _seed_alerts(db, Alert):
    if Alert.query.count() > 0:
        return

    now = datetime.utcnow()
    alerts = [
        Alert(title="SSH brute force — 18 attempts / 60s",
              description="18 failed SSH login attempts were detected from 192.168.1.10 within 60 seconds. "
                          "This matches an automated brute force attack. The IP has an AbuseIPDB score of 87 — "
                          "a known malicious host. Block this IP at the firewall immediately and check whether "
                          "any login attempt succeeded.",
              severity="critical", severity_score=5,
              rule_name="ssh_brute_force", source_ip="192.168.1.10",
              log_type="syslog", status="open",
              abuse_score=87, abuse_country="RU", abuse_checked=True,
              created_at=now - timedelta(minutes=2)),

        Alert(title="New service installed (Event 7045)",
              description="A new Windows service was installed on DESKTOP-WIN10. Event ID 7045 is a common "
                          "persistence mechanism used by malware and ransomware to survive reboots. "
                          "Investigate the service name and binary path immediately.",
              severity="critical", severity_score=5,
              rule_name="windows_service_install", source_ip="10.10.10.44",
              log_type="evtx", status="open",
              abuse_score=62, abuse_country="CN", abuse_checked=True,
              created_at=now - timedelta(minutes=8)),

        Alert(title="Account lockout — Administrator (Event 4740)",
              description="The Administrator account was locked out after repeated failed login attempts. "
                          "This is likely a continuation of the brute force attack from 192.168.1.10. "
                          "Check linked alerts and open an incident if not already done.",
              severity="high", severity_score=4,
              rule_name="account_lockout", source_ip="192.168.1.10",
              log_type="evtx", status="in_progress",
              abuse_score=87, abuse_country="RU", abuse_checked=True,
              created_at=now - timedelta(minutes=15)),

        Alert(title="Explicit credential logon (Event 4648)",
              description="A logon was attempted using explicit credentials from a process running as a "
                          "different user. This can indicate lateral movement or credential theft. "
                          "Review the source process and target account.",
              severity="high", severity_score=4,
              rule_name="explicit_credential_logon", source_ip="172.16.0.5",
              log_type="evtx", status="open",
              abuse_score=12, abuse_country="GB", abuse_checked=True,
              created_at=now - timedelta(minutes=22)),

        Alert(title="Sudo failure — root escalation attempt",
              description="A user attempted to run a privileged sudo command and failed authentication. "
                          "Repeated sudo failures may indicate an insider threat or a compromised account "
                          "attempting privilege escalation.",
              severity="high", severity_score=4,
              rule_name="sudo_failure", source_ip="10.0.0.8",
              log_type="syslog", status="open",
              abuse_score=5, abuse_country="GB", abuse_checked=True,
              created_at=now - timedelta(minutes=28)),

        Alert(title="Path traversal attempt — /../etc/passwd",
              description="A directory traversal sequence was detected in the HTTP request path targeting "
                          "/etc/passwd. This is a classic LFI probe. The IP has a very high AbuseIPDB "
                          "score of 95 suggesting an automated scanner.",
              severity="medium", severity_score=3,
              rule_name="path_traversal", source_ip="203.0.113.9",
              log_type="apache", status="false_positive",
              abuse_score=95, abuse_country="NL", abuse_checked=True,
              created_at=now - timedelta(minutes=34)),

        Alert(title="Failed logins ×6 — invalid user",
              description="Six failed SSH login attempts for non-existent usernames were recorded from "
                          "192.168.1.10. Username enumeration often precedes a targeted brute force attack.",
              severity="medium", severity_score=3,
              rule_name="ssh_brute_force", source_ip="192.168.1.10",
              log_type="syslog", status="open",
              abuse_score=87, abuse_country="RU", abuse_checked=True,
              created_at=now - timedelta(minutes=41)),

        Alert(title="Off-hours login — 03:14 UTC",
              description="A successful login occurred at 03:14 UTC, outside normal working hours. "
                          "This may be legitimate remote access or an indicator of a compromised account. "
                          "Verify with the user.",
              severity="low", severity_score=2,
              rule_name="ssh_brute_force", source_ip="10.0.0.22",
              log_type="syslog", status="open",
              abuse_score=3, abuse_country="GB", abuse_checked=True,
              created_at=now - timedelta(hours=1)),

        Alert(title="HTTP 403 flood — /admin (×42)",
              description="42 HTTP 403 responses were returned to 203.0.113.9 probing the /admin endpoint. "
                          "Likely an automated web scanner. The endpoint is properly protected.",
              severity="low", severity_score=2,
              rule_name="http_scanner", source_ip="203.0.113.9",
              log_type="apache", status="closed",
              abuse_score=95, abuse_country="NL", abuse_checked=True,
              created_at=now - timedelta(hours=2)),
    ]
    db.session.add_all(alerts)
    db.session.commit()
    logger.info(f"Seeded {len(alerts)} alerts.")


def _seed_incidents(db, Incident, IncidentNote, IncidentAudit, Alert):
    if Incident.query.count() > 0:
        return

    now = datetime.utcnow()

    # Incident 1
    inc1 = Incident(
        title="Brute force cluster — web01",
        description="Multiple alerts linked to 192.168.1.10 indicate an active brute force campaign "
                    "against web01. SSH is being targeted with automated tooling.",
        severity="critical", status="investigating", analyst="Alice",
        created_at=now - timedelta(minutes=25),
        updated_at=now - timedelta(minutes=10),
    )
    db.session.add(inc1)
    db.session.flush()   # get inc1.id

    db.session.add_all([
        IncidentNote(content="IP blocked at firewall. Checking auth logs for any successful logins.",
                     author="Alice", incident_id=inc1.id,
                     created_at=now - timedelta(minutes=18)),
        IncidentNote(content="No successful logins confirmed. Monitoring for further attempts from different IPs.",
                     author="Alice", incident_id=inc1.id,
                     created_at=now - timedelta(minutes=10)),
        IncidentAudit(action="Incident created", user="Alice", incident_id=inc1.id,
                      created_at=now - timedelta(minutes=25)),
        IncidentAudit(action="Status: new → triaged", user="Alice", incident_id=inc1.id,
                      created_at=now - timedelta(minutes=22)),
        IncidentAudit(action="Status: triaged → investigating", user="Alice", incident_id=inc1.id,
                      created_at=now - timedelta(minutes=18)),
    ])

    # Link alerts 1, 3, 7 to incident 1
    Alert.query.filter(Alert.id.in_([1, 3, 7])).update(
        {"incident_id": inc1.id}, synchronize_session="fetch"
    )

    # Incident 2
    inc2 = Incident(
        title="Suspicious service installation",
        description="A new Windows service was installed on DESKTOP-WIN10. Potentially a persistence "
                    "mechanism. Isolating host for investigation.",
        severity="high", status="triaged", analyst="Bob",
        created_at=now - timedelta(minutes=20),
        updated_at=now - timedelta(minutes=12),
    )
    db.session.add(inc2)
    db.session.flush()

    db.session.add_all([
        IncidentNote(content="Service name: WindowsUpdateHelper. Binary path: C:\\Users\\Public\\svchost32.exe — highly suspicious.",
                     author="Bob", incident_id=inc2.id,
                     created_at=now - timedelta(minutes=15)),
        IncidentAudit(action="Incident created", user="Bob", incident_id=inc2.id,
                      created_at=now - timedelta(minutes=20)),
        IncidentAudit(action="Status: new → triaged", user="Bob", incident_id=inc2.id,
                      created_at=now - timedelta(minutes=16)),
    ])
    Alert.query.filter(Alert.id == 2).update(
        {"incident_id": inc2.id}, synchronize_session="fetch"
    )

    # Incident 3
    inc3 = Incident(
        title="Account lockout — Finance PC",
        description="Administrator account lockout on Finance PC. Possibly related to brute force "
                    "activity. Needs assignment.",
        severity="high", status="new", analyst=None,
        created_at=now - timedelta(minutes=10),
        updated_at=now - timedelta(minutes=10),
    )
    db.session.add(inc3)
    db.session.flush()

    db.session.add(
        IncidentAudit(action="Incident created", user="System", incident_id=inc3.id,
                      created_at=now - timedelta(minutes=10))
    )

    db.session.commit()
    logger.info("Seeded 3 incidents.")
