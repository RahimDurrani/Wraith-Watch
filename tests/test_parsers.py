import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from utils.parsers import (
    detect_format,
    parse_apache_line,
    parse_syslog_line,
    parse_lines,
)


# ── detect_format ─────────────────────────────────────────────────────────────

class TestDetectFormat:
    def test_detects_evtx_by_extension(self):
        assert detect_format("Security.evtx", "") == "evtx"

    def test_detects_apache_by_content(self):
        line = '192.168.1.10 - - "GET /index.html HTTP/1.1" 200 1024'
        assert detect_format("access.log", line) == "apache"

    def test_detects_syslog_by_month_prefix(self):
        line = "Jun  4 09:23:01 webserver sshd[1234]: Failed password for root"
        assert detect_format("auth.log", line) == "syslog"

    def test_returns_unknown_for_unrecognised(self):
        assert detect_format("data.csv", "hello world") == "unknown"


# ── Apache parser ─────────────────────────────────────────────────────────────

class TestApacheParser:
    def test_parses_standard_combined_log(self):
        line = '192.168.1.10 - - "GET /index.html HTTP/1.1" 200 2048'
        result = parse_apache_line(line)
        assert result is not None
        assert result["source_ip"] == "192.168.1.10"
        assert result["status"]    == 200
        assert result["path"]      == "/index.html"
        assert result["method"]    == "GET"

    def test_flags_403_as_suspicious(self):
        line = '192.168.1.10 - - "GET /admin HTTP/1.1" 403 512'
        result = parse_apache_line(line)
        assert result is not None
        assert result["flagged"] is True

    def test_flags_path_traversal(self):
        line = '203.0.113.9 - - "GET /../etc/passwd HTTP/1.1" 400 0'
        result = parse_apache_line(line)
        assert result is not None
        assert result["flagged"] is True

    def test_does_not_flag_normal_200(self):
        line = '10.0.0.5 - - "GET /about.html HTTP/1.1" 200 1024'
        result = parse_apache_line(line)
        assert result is not None
        assert result["flagged"] is False

    def test_flags_wp_admin_probe(self):
        line = '203.0.113.9 - - "GET /wp-admin HTTP/1.1" 404 0'
        result = parse_apache_line(line)
        assert result is not None
        assert result["flagged"] is True

    def test_returns_none_for_blank_line(self):
        assert parse_apache_line("") is None

    def test_returns_none_for_comment(self):
        assert parse_apache_line("# This is a comment") is None


# ── Syslog parser ─────────────────────────────────────────────────────────────

class TestSyslogParser:
    def test_parses_failed_password(self):
        line = "Jun  4 09:23:01 webserver sshd[1234]: Failed password for root from 192.168.1.10 port 22 ssh2"
        result = parse_syslog_line(line)
        assert result is not None
        assert result["source_ip"]  == "192.168.1.10"
        assert result["hostname"]   == "webserver"
        assert result["process"]    == "sshd"
        assert result["flagged"]    is True
        assert result["event"]      == "failed_login"

    def test_parses_accepted_login(self):
        line = "Jun  4 09:24:00 webserver sshd[5678]: Accepted password for deploy from 10.0.0.2 port 54321 ssh2"
        result = parse_syslog_line(line)
        assert result is not None
        assert result["flagged"]    is False
        assert result["event"]      == "login_ok"

    def test_parses_breakin_attempt(self):
        line = "Jun  4 09:27:00 webserver sshd[1111]: POSSIBLE BREAK-IN ATTEMPT from 10.10.10.10"
        result = parse_syslog_line(line)
        assert result is not None
        assert result["flagged"]    is True
        assert result["event"]      == "breakin"

    def test_extracts_ip_from_message(self):
        line = "Jun  4 09:23:01 server sshd[1]: Failed password for root from 10.0.0.5 port 22 ssh2"
        result = parse_syslog_line(line)
        assert result["source_ip"] == "10.0.0.5"

    def test_returns_none_for_blank(self):
        assert parse_syslog_line("") is None

    def test_returns_none_for_unrecognised(self):
        assert parse_syslog_line("This does not match any known format") is None

    def test_parses_sudo_failure(self):
        line = "Jun  4 09:25:10 server sudo[9012]: alice : incorrect password attempt"
        result = parse_syslog_line(line)
        assert result is not None


# ── Batch parser ──────────────────────────────────────────────────────────────

class TestParseLines:
    def test_parses_multiple_apache_lines(self):
        lines = [
            '192.168.1.10 - - "GET /admin HTTP/1.1" 403 512\n',
            '10.0.0.5 - - "GET /index.html HTTP/1.1" 200 2048\n',
            '',
        ]
        results = parse_lines(lines, "apache")
        assert len(results) == 2

    def test_parses_multiple_syslog_lines(self):
        lines = [
            "Jun  4 09:23:01 webserver sshd[1234]: Failed password for root from 192.168.1.10 port 22 ssh2\n",
            "Jun  4 09:24:00 webserver sshd[5678]: Accepted password for deploy from 10.0.0.2 port 54321 ssh2\n",
        ]
        results = parse_lines(lines, "syslog")
        assert len(results) == 2
        assert results[0]["flagged"] is True
        assert results[1]["flagged"] is False

    def test_skips_blank_lines(self):
        lines = ["", "  ", "\n"]
        results = parse_lines(lines, "apache")
        assert len(results) == 0
