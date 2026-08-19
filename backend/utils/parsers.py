import re

# ── Format detection 
def detect_format(filename: str, first_line: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "evtx":
        return "evtx"
    line = first_line.strip()
    if line and line[0].isdigit() and '"' in line and "HTTP" in line:
        return "apache"
    months = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
    if line[:3] in months or line.startswith("<"):
        return "syslog"
    return "unknown"


# ── Apache parser
_APACHE_RE = re.compile(
    r'(?P<source_ip>\S+)\s+-\s+-\s+'
    r'"(?P<method>\w+)\s+(?P<path>\S+)\s+HTTP/[\d.]+"\s+'
    r'(?P<status>\d{3})\s+(?P<bytes>\S+)'
)
_SCAN_RE = re.compile(
    r'\.env$|wp-admin|phpmyadmin|\.\./|union.*select|<script|eval\(|etc/passwd|/\.git/',
    re.I
)


def parse_apache_line(line: str) -> dict | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = _APACHE_RE.search(line)
    if not m:
        return None
    g = m.groupdict()
    status  = int(g["status"])
    path    = g["path"]
    flagged = status >= 400 or bool(_SCAN_RE.search(path))
    return {
        "source_ip":  g["source_ip"],
        "method":     g["method"],
        "path":       path,
        "status":     status,
        "flagged":    flagged,
        "raw":        line,
        "raw_message": line,
    }


# ── Syslog parser 
_SYSLOG_RE = re.compile(
    r'^(?:<\d+>)?(?P<month>\w{3})\s+(?P<day>\s?\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
    r'(?P<hostname>\S+)\s+(?P<process>\S+?)(?:\[\d+\])?:\s+(?P<msg>.+)$'
)
_IP_RE = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')
_SYSLOG_FLAGS = [
    (re.compile(r'Failed password',             re.I), True,  "failed_login"),
    (re.compile(r'Invalid user',                re.I), True,  "invalid_user"),
    (re.compile(r'POSSIBLE BREAK-IN ATTEMPT',   re.I), True,  "breakin"),
    (re.compile(r'sudo.*incorrect password|sudo.*authentication failure', re.I), True, "sudo_fail"),
    (re.compile(r'Out of memory',               re.I), True,  "oom"),
    (re.compile(r'Accepted (password|publickey)', re.I), False, "login_ok"),
]


def parse_syslog_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    m = _SYSLOG_RE.match(line)
    if not m:
        return None
    g        = m.groupdict()
    msg      = g["msg"]
    ip_match = _IP_RE.search(msg)
    flagged, event = False, None
    for pattern, flag, etype in _SYSLOG_FLAGS:
        if pattern.search(msg):
            flagged, event = flag, etype
            break
    return {
        "source_ip":   ip_match.group(1) if ip_match else None,
        "hostname":    g["hostname"],
        "process":     g["process"],
        "message":     msg,
        "flagged":     flagged,
        "event":       event,
        "raw":         line,
        "raw_message": line,
    }


# ── Batch parser 
def parse_lines(lines: list, fmt: str) -> list:
    results = []
    for line in lines:
        if not (line or "").strip():
            continue
        if fmt == "apache":
            parsed = parse_apache_line(line)
        elif fmt == "syslog":
            parsed = parse_syslog_line(line)
        else:
            parsed = None
        if parsed:
            results.append(parsed)
    return results
