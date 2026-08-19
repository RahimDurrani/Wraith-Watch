import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest


# ── Input sanitisation ────────────────────────────────────────────────────────

class TestSanitise:
    def test_strips_script_tag(self):
        from utils.security import sanitise
        dirty = '<script>alert("xss")</script>Hello'
        clean = sanitise(dirty)
        assert "<script>" not in clean
        assert "Hello" in clean

    def test_strips_html_tags(self):
        from utils.security import sanitise
        assert sanitise("<b>bold</b>") == "bold"
        assert sanitise('<a href="evil.com">link</a>') == "link"

    def test_strips_img_onerror(self):
        from utils.security import sanitise
        dirty = '<img src=x onerror="alert(1)">note text'
        clean = sanitise(dirty)
        assert "onerror" not in clean
        assert "note text" in clean

    def test_preserves_plain_text(self):
        from utils.security import sanitise
        assert sanitise("Blocked the IP at the firewall.") == "Blocked the IP at the firewall."

    def test_handles_empty(self):
        from utils.security import sanitise
        assert sanitise("") == ""
        assert sanitise(None) == ""


# ── Rate limiting ─────────────────────────────────────────────────────────────

class TestRateLimit:
    def setup_method(self):
        # Clear the rate limit state before each test
        from utils.security import _login_attempts
        _login_attempts.clear()

    def test_allows_under_limit(self):
        from utils.security import check_rate_limit, record_failed_attempt
        ip = "10.0.0.1"
        for _ in range(4):
            record_failed_attempt(ip)
        allowed, retry = check_rate_limit(ip)
        assert allowed is True

    def test_blocks_at_limit(self):
        from utils.security import check_rate_limit, record_failed_attempt
        ip = "10.0.0.2"
        for _ in range(5):
            record_failed_attempt(ip)
        allowed, retry = check_rate_limit(ip)
        assert allowed is False
        assert retry > 0

    def test_clear_resets(self):
        from utils.security import check_rate_limit, record_failed_attempt, clear_attempts
        ip = "10.0.0.3"
        for _ in range(5):
            record_failed_attempt(ip)
        clear_attempts(ip)
        allowed, _ = check_rate_limit(ip)
        assert allowed is True

    def test_separate_ips_independent(self):
        from utils.security import check_rate_limit, record_failed_attempt
        for _ in range(5):
            record_failed_attempt("10.0.0.4")
        # A different IP should still be allowed
        allowed, _ = check_rate_limit("10.0.0.5")
        assert allowed is True


# ── RBAC decorator ────────────────────────────────────────────────────────────

class TestRBAC:
    @pytest.fixture
    def flask_app(self):
        from flask import Flask, request, jsonify
        from utils.security import role_required
        app = Flask(__name__)

        @app.route("/admin")
        def admin_route():
            # Simulate login_required having set request.user
            from utils.security import role_required
            return jsonify({"ok": True})

        return app

    def test_admin_allowed(self):
        from flask import Flask, request, jsonify
        from utils.security import role_required
        app = Flask(__name__)

        @app.route("/x")
        @role_required("admin")
        def protected():
            return jsonify({"ok": True})

        with app.test_request_context("/x"):
            request.user = {"role": "admin"}
            resp = protected()
            # Successful call returns a Response, not a tuple
            assert not isinstance(resp, tuple)

    def test_analyst_denied_admin_route(self):
        from flask import Flask, request, jsonify
        from utils.security import role_required
        app = Flask(__name__)

        @app.route("/y")
        @role_required("admin")
        def protected():
            return jsonify({"ok": True})

        with app.test_request_context("/y"):
            request.user = {"role": "analyst"}
            resp = protected()
            # Denied returns a (response, 403) tuple
            assert isinstance(resp, tuple)
            assert resp[1] == 403

    def test_no_user_denied(self):
        from flask import Flask, request, jsonify
        from utils.security import role_required
        app = Flask(__name__)

        @app.route("/z")
        @role_required("admin")
        def protected():
            return jsonify({"ok": True})

        with app.test_request_context("/z"):
            resp = protected()
            assert isinstance(resp, tuple)
            assert resp[1] == 401
