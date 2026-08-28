from flask           import Blueprint, jsonify, request
from models.database import db, DetectionRule

rules_bp = Blueprint("rules", __name__, url_prefix="/api")


BUILTIN_RULES = [
    {"name": "ssh_brute_force",           "description": "Multiple failed SSH login attempts from the same IP within a short window — the signature of an automated brute force attack.", "pattern": "Failed password | authentication failure | Invalid user", "log_type": "syslog", "severity": "critical", "threshold": 5,  "window_seconds": 60},
    {"name": "windows_service_install",   "description": "A new Windows service was installed (Event 7045) — a common malware and ransomware persistence mechanism.",                  "pattern": "EventID 7045 | new service was installed",              "log_type": "evtx",   "severity": "critical", "threshold": None, "window_seconds": None},
    {"name": "breakin_attempt",           "description": "sshd reported a possible break-in attempt — the remote host's DNS name does not match its IP, indicating spoofing.",           "pattern": "POSSIBLE BREAK-IN ATTEMPT | BREAK-IN",                  "log_type": "syslog", "severity": "critical", "threshold": None, "window_seconds": None},
    {"name": "new_process_created",       "description": "A new process was created from a suspicious location such as Temp, Public, or AppData (Event 4688).",                          "pattern": "EventID 4688 .* (Temp|Public|AppData|svchost32|cmd|powershell)", "log_type": "evtx", "severity": "critical", "threshold": None, "window_seconds": None},
    {"name": "account_lockout",           "description": "A user account was locked out (Event 4740), often the result of repeated failed logins during a brute force attack.",           "pattern": "EventID 4740 | account was locked out",                 "log_type": "evtx",   "severity": "high",     "threshold": None, "window_seconds": None},
    {"name": "explicit_credential_logon", "description": "A logon using explicit credentials from a different user context (Event 4648) — a possible sign of lateral movement.",           "pattern": "EventID 4648 | Logon using explicit credentials",       "log_type": "evtx",   "severity": "high",     "threshold": None, "window_seconds": None},
    {"name": "sudo_failure",              "description": "A failed sudo privilege escalation attempt, which may indicate an insider threat or a compromised account.",                    "pattern": "sudo .* incorrect password | sudo .* authentication failure", "log_type": "syslog", "severity": "high", "threshold": None, "window_seconds": None},
    {"name": "sql_injection_attempt",     "description": "A SQL injection pattern was detected in an HTTP request, an attempt to manipulate database queries.",                          "pattern": "union select | drop table | 1=1 | or '1'='1",           "log_type": "apache", "severity": "high",     "threshold": None, "window_seconds": None},
    {"name": "path_traversal",            "description": "A directory traversal sequence was detected in an HTTP request path, targeting files outside the web root.",                    "pattern": "../ | ..%2F | etc/passwd | /etc/shadow",                "log_type": "apache", "severity": "medium",   "threshold": None, "window_seconds": None},
    {"name": "http_scanner",              "description": "An automated web scanner was detected probing common vulnerable paths such as /wp-admin or /.env.",                             "pattern": "GET .* (wp-admin|phpmyadmin|.env|.git|admin.php)",      "log_type": "apache", "severity": "low",      "threshold": 10, "window_seconds": 120},
]


def seed_rules(app):
    """Seed the detection_rules table with the 10 built-in rules on first run."""
    with app.app_context():
        if DetectionRule.query.count() > 0:
            return
        for r in BUILTIN_RULES:
            db.session.add(DetectionRule(
                name=r["name"], description=r["description"], pattern=r["pattern"],
                log_type=r["log_type"], severity=r["severity"],
                threshold=r["threshold"], window_seconds=r["window_seconds"],
                is_enabled=True,
            ))
        db.session.commit()


@rules_bp.route("/rules")
def list_rules():
    rules = DetectionRule.query.order_by(DetectionRule.id).all()
    return jsonify([r.to_dict() for r in rules])


@rules_bp.route("/rules/<int:rid>/toggle", methods=["PATCH"])
def toggle_rule(rid):
    rule = DetectionRule.query.get_or_404(rid)
    rule.is_enabled = not rule.is_enabled
    db.session.commit()
    return jsonify(rule.to_dict())
