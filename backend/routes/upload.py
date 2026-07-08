# backend/routes/upload.py
# ─────────────────────────────────────────────────────────
# Log file upload — now saves parsed entries to DB,
# runs the rule engine, and enriches alerts with AbuseIPDB.
# ─────────────────────────────────────────────────────────

import os
from datetime        import datetime
from flask           import Blueprint, request, jsonify, current_app
from werkzeug.utils  import secure_filename
from models.database import db, LogEntry, LogSource, Alert
from utils.parsers   import detect_format, parse_lines
from utils.rule_engine import run_rules
from utils.ip_reputation import enrich_alert

upload_bp = Blueprint("upload", __name__, url_prefix="/api")
ALLOWED_EXTENSIONS = {"log", "txt", "evtx"}

_upload_history = []   # session-level upload history list


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route("/upload", methods=["POST"])
def upload_log():
    if "file" not in request.files:
        return jsonify({"error": "No file field in request"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected"}), 400
    if not _allowed(f.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    filename  = secure_filename(f.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    f.save(save_path)

    # ── Read and detect format ────────────────────────────────────────────────
    with open(save_path, "r", encoding="utf-8", errors="replace") as fh:
        raw_lines = fh.readlines()

    first_line = next((l for l in raw_lines if l.strip()), "")
    fmt        = detect_format(filename, first_line)

    if fmt == "unknown":
        return jsonify({"error": "Could not detect log format. Expected Apache, syslog, or .evtx"}), 400

    # ── Parse all lines ───────────────────────────────────────────────────────
    parsed = parse_lines(raw_lines, fmt)

    # ── Save to database ──────────────────────────────────────────────────────
    saved_count  = 0
    alert_count  = 0
    flagged_sample = []

    for entry in parsed:
        # Save log entry to DB
        log = LogEntry(
            source_ip   = entry.get("source_ip"),
            timestamp   = datetime.utcnow(),
            log_type    = fmt,
            raw_message = entry.get("raw", entry.get("raw_message", "")),
            hostname    = entry.get("hostname"),
            source_name = filename,
        )
        db.session.add(log)
        db.session.flush()   # get log.id

        # Attach log_id to the entry dict for the rule engine
        entry["log_id"] = log.id
        saved_count += 1

    db.session.commit()

    # ── Run rule engine on each entry ─────────────────────────────────────────
    for entry in parsed:
        fired = run_rules(entry, db, Alert)
        for alert in fired:
            enrich_alert(alert, db)
            alert_count += 1
            if len(flagged_sample) < 10:
                flagged_sample.append({
                    "source_ip": entry.get("source_ip"),
                    "flagged":   True,
                    "raw":       entry.get("raw", entry.get("raw_message", ""))[:120],
                })

    # ── Update log source last_seen ───────────────────────────────────────────
    source = LogSource.query.filter_by(name=filename).first()
    if source:
        source.last_seen  = datetime.utcnow()
        source.total_logs += saved_count
    else:
        source = LogSource(
            name        = filename,
            source_type = fmt,
            last_seen   = datetime.utcnow(),
            total_logs  = saved_count,
        )
        db.session.add(source)
    db.session.commit()

    record = {
        "filename":    filename,
        "format":      fmt,
        "uploaded_at": datetime.utcnow().isoformat(),
        "total_lines": len(raw_lines),
        "parsed":      saved_count,
        "flagged":     alert_count,
        "sample":      flagged_sample,
    }
    _upload_history.append(record)
    return jsonify({"success": True, **record})


@upload_bp.route("/uploads")
def upload_history():
    return jsonify(list(reversed(_upload_history)))
