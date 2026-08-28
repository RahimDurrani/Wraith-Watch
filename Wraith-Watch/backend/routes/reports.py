from flask           import Blueprint, jsonify, request, Response
from models.database import db, Incident, Alert, LogEntry
from utils.pdf_report import generate_incident_pdf
from utils.ip_reputation import check_ip
from utils.security  import sanitise
import re

reports_bp = Blueprint("reports", __name__, url_prefix="/api")

_IP_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")


@reports_bp.route("/incidents/<int:iid>/report")
def incident_report(iid):
    """Generate and download a forensic PDF report for an incident."""
    incident = Incident.query.get_or_404(iid)
    alerts = Alert.query.filter_by(incident_id=iid).order_by(
        Alert.severity_score.desc()).all()

    pdf_bytes = generate_incident_pdf(incident, alerts)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="incident_INC-{iid:03d}.pdf"',
        },
    )


@reports_bp.route("/logs/search")
def log_search():
    """
    Full-text search across stored log entries.

    Query params:
      q         - search term (matched against raw_message, source_ip, hostname)
      log_type  - optional filter: apache | syslog | evtx
      limit     - max results (default 100)
      offset    - pagination offset (default 0)
    """
    q = (request.args.get("q", "") or "").strip()
    log_type = request.args.get("log_type", "").strip()
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))

    query = LogEntry.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                LogEntry.raw_message.ilike(like),
                LogEntry.source_ip.ilike(like),
                LogEntry.hostname.ilike(like),
                LogEntry.source_name.ilike(like),
            )
        )
    if log_type:
        query = query.filter_by(log_type=log_type)

    total = query.count()
    results = query.order_by(LogEntry.ingested_at.desc()) \
                   .offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "count": len(results),
        "offset": offset,
        "limit": limit,
        "results": [r.to_dict() for r in results],
    })


@reports_bp.route("/incidents/from-log", methods=["POST"])
def incident_from_log():
    """
    Create an incident directly from a live log entry.
    Called by the 'Create incident from this log' button.
    """
    from models.database import IncidentAudit
    data = request.get_json(silent=True) or {}
    message = sanitise((data.get("message") or "").strip())
    log_type = (data.get("log_type") or "").strip().lower()
    hostname = sanitise((data.get("hostname") or "").strip())
    flag_level = (data.get("flag_level") or "medium").strip().lower()
    source_ip = data.get("source_ip")

    if not message:
        return jsonify({"error": "Log message is required."}), 400

    # Extract IP from the message if not provided
    if not source_ip:
        m = _IP_RE.search(message)
        source_ip = m.group(1) if m else None

    if flag_level not in ("info", "low", "medium", "high", "critical"):
        flag_level = "medium"

    # Build a readable title from the log
    short = message[:60] + ("…" if len(message) > 60 else "")
    title = f"Investigation: {short}"

    incident = Incident(
        title = title,
        description = f"Incident raised from a {log_type or 'log'} entry on "
                      f"{hostname or 'unknown host'}:\n\n{message}",
        severity = flag_level,
        status = "new",
        analyst = None,
    )
    db.session.add(incident)
    db.session.flush()

    db.session.add(IncidentAudit(
        incident_id = incident.id,
        action = "Incident created from live log entry",
        user = "analyst",
    ))
    db.session.commit()
    return jsonify(incident.to_dict()), 201


@reports_bp.route("/ip-lookup")
def ip_lookup():
    """
    On-demand AbuseIPDB lookup for a single IP.
    Called by the 'Look up IP in AbuseIPDB' button.
    """
    ip = (request.args.get("ip") or "").strip()
    if not ip:
        return jsonify({"error": "No IP provided."}), 400

    result = check_ip(ip)
    if result is None:
        # Either private IP, no API key, or lookup failed
        return jsonify({
            "ip": ip,
            "available": False,
            "message": "No reputation data (private IP, or no AbuseIPDB API key configured).",
        })
    return jsonify({
        "ip": ip,
        "available": True,
        "abuse_score": result["abuse_score"],
        "abuse_country": result["abuse_country"],
    })
