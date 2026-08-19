import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from flask      import Flask
from flask_bcrypt import Bcrypt


@pytest.fixture
def app():
    """Create a Flask test app with an in-memory SQLite database."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"]                        = True
    app.config["STALE_SOURCE_MINUTES"]           = 5

    from models.database import db
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def ctx(app):
    """Push an app context for direct DB access in tests."""
    with app.app_context():
        yield


# ── Rule engine ───────────────────────────────────────────────────────────────

class TestRuleEngine:

    def test_ssh_brute_force_fires_at_threshold(self, app):
        """Brute force rule should fire after 5 failed logins from the same IP."""
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules, _event_window

            # Clear any leftover window state
            _event_window.clear()

            entry = {
                "raw_message": "Failed password for root from 192.168.1.10 port 22 ssh2",
                "log_type":    "syslog",
                "source_ip":   "192.168.1.10",
            }

            # First 4 should not fire
            for i in range(4):
                alerts = run_rules(entry, db, Alert)
                assert len(alerts) == 0, f"Fired too early on attempt {i+1}"

            # 5th should fire
            alerts = run_rules(entry, db, Alert)
            assert len(alerts) == 1
            assert alerts[0].rule_name == "ssh_brute_force"
            assert alerts[0].severity  == "critical"

    def test_windows_service_install_fires_immediately(self, app):
        """Service install rule has no threshold — fires on first match."""
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": "EventID 7045: A new service was installed. ServiceName: WindowsUpdateHelper",
                "log_type":    "evtx",
                "source_ip":   "10.10.10.44",
            }
            alerts = run_rules(entry, db, Alert)
            assert len(alerts) == 1
            assert alerts[0].rule_name == "windows_service_install"
            assert alerts[0].severity  == "critical"

    def test_path_traversal_fires(self, app):
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": '203.0.113.9 - - "GET /../etc/passwd HTTP/1.1" 400 0',
                "log_type":    "apache",
                "source_ip":   "203.0.113.9",
            }
            alerts = run_rules(entry, db, Alert)
            assert any(a.rule_name == "path_traversal" for a in alerts)

    def test_sql_injection_fires(self, app):
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": '192.168.1.5 - - "GET /login?id=1 UNION SELECT * FROM users HTTP/1.1" 200 512',
                "log_type":    "apache",
                "source_ip":   "192.168.1.5",
            }
            alerts = run_rules(entry, db, Alert)
            assert any(a.rule_name == "sql_injection_attempt" for a in alerts)

    def test_breakin_fires(self, app):
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": "sshd[1111]: POSSIBLE BREAK-IN ATTEMPT from 10.10.10.10",
                "log_type":    "syslog",
                "source_ip":   "10.10.10.10",
            }
            alerts = run_rules(entry, db, Alert)
            assert any(a.rule_name == "breakin_attempt" for a in alerts)

    def test_normal_log_fires_no_rules(self, app):
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": '10.0.0.5 - - "GET /index.html HTTP/1.1" 200 2048',
                "log_type":    "apache",
                "source_ip":   "10.0.0.5",
            }
            alerts = run_rules(entry, db, Alert)
            assert len(alerts) == 0

    def test_rule_skips_wrong_log_type(self, app):
        """Syslog rules should not fire on Apache entries even if pattern matches."""
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": "Failed password for root from 192.168.1.10",
                "log_type":    "apache",   # wrong type for ssh_brute_force
                "source_ip":   "192.168.1.10",
            }
            alerts = run_rules(entry, db, Alert)
            # Should not fire ssh_brute_force (syslog only)
            assert not any(a.rule_name == "ssh_brute_force" for a in alerts)

    def test_alert_saved_to_database(self, app):
        """Fired alerts should be persisted in the DB."""
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": "EventID 4740: A user account was locked out. TargetUser: Administrator",
                "log_type":    "evtx",
                "source_ip":   "192.168.1.10",
            }
            alerts = run_rules(entry, db, Alert)
            assert len(alerts) >= 1
            # Verify it's actually in the DB
            db_alert = Alert.query.filter_by(rule_name="account_lockout").first()
            assert db_alert is not None
            assert db_alert.severity == "high"

    def test_alert_severity_score_set(self, app):
        with app.app_context():
            from models.database import db, Alert
            from utils.rule_engine import run_rules

            entry = {
                "raw_message": "EventID 7045: new service was installed",
                "log_type":    "evtx",
                "source_ip":   "10.0.0.1",
            }
            alerts = run_rules(entry, db, Alert)
            assert alerts[0].severity_score == 5   # critical = 5
