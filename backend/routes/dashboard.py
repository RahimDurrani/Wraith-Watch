# backend/routes/dashboard.py
# ─────────────────────────────────────────────────────────
# Core SIEM data routes — now using SQLAlchemy DB queries
# instead of hardcoded lists.
# ─────────────────────────────────────────────────────────

from flask           import Blueprint, jsonify, request
from models.database import db, Alert, Incident, LogSource
from datetime        import datetime

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


@dashboard_bp.route("/stats")
def stats():
    open_alerts    = Alert.query.filter_by(status="open").count()
    critical       = Alert.query.filter_by(severity="critical").count()
    open_incidents = Incident.query.filter(Incident.status != "closed").count()
    total_sources  = LogSource.query.count()
    active_sources = len([s for s in LogSource.query.all() if s.health_status() == "active"])
    stale_sources  = len([s for s in LogSource.query.all() if s.health_status() == "stale"])
    return jsonify({
        "open_alerts":    open_alerts,
        "critical":       critical,
        "open_incidents": open_incidents,
        "log_sources":    total_sources,
        "active_sources": active_sources,
        "stale_sources":  stale_sources,
    })


@dashboard_bp.route("/alerts")
def alerts():
    sev = request.args.get("severity", "")
    src = request.args.get("log_type", "")
    q   = Alert.query
    if sev: q = q.filter_by(severity=sev)
    if src: q = q.filter_by(log_type=src)
    results = q.order_by(Alert.severity_score.desc(), Alert.created_at.desc()).all()
    return jsonify([a.to_dict() for a in results])


@dashboard_bp.route("/alerts/<int:aid>")
def alert_detail(aid):
    a = Alert.query.get_or_404(aid)
    return jsonify(a.to_dict())


@dashboard_bp.route("/incidents")
def incidents():
    results = Incident.query.order_by(Incident.created_at.desc()).all()
    return jsonify([i.to_dict() for i in results])


@dashboard_bp.route("/incidents/<int:iid>")
def incident_detail(iid):
    i = Incident.query.get_or_404(iid)
    return jsonify(i.to_dict())


@dashboard_bp.route("/incidents/<int:iid>/status", methods=["PATCH"])
def update_incident_status(iid):
    """Advance incident status through the workflow."""
    from models.database import IncidentAudit
    inc  = Incident.query.get_or_404(iid)
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in Incident.STATUS_FLOW:
        return jsonify({"error": "Invalid status"}), 400

    old_status = inc.status
    inc.status  = new_status
    inc.updated_at = datetime.utcnow()
    if new_status == "closed":
        inc.closed_at = datetime.utcnow()

    audit = IncidentAudit(
        incident_id=inc.id,
        action=f"Status: {old_status} → {new_status}",
        user=data.get("analyst", "analyst"),
    )
    db.session.add(audit)
    db.session.commit()
    return jsonify(inc.to_dict())


@dashboard_bp.route("/incidents/<int:iid>/notes", methods=["POST"])
def add_incident_note(iid):
    """Add an analyst note to an incident."""
    from models.database import IncidentNote, IncidentAudit
    inc  = Incident.query.get_or_404(iid)
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    author  = data.get("author", "analyst")
    if not content:
        return jsonify({"error": "Note content required"}), 400

    note  = IncidentNote(content=content, author=author, incident_id=inc.id)
    audit = IncidentAudit(
        incident_id=inc.id,
        action=f"Note added by {author}",
        user=author,
    )
    db.session.add_all([note, audit])
    db.session.commit()
    return jsonify(note.to_dict()), 201


@dashboard_bp.route("/log-sources")
def log_sources():
    sources = LogSource.query.filter_by(is_active=True).all()
    return jsonify([s.to_dict() for s in sources])


@dashboard_bp.route("/log-sources/<int:sid>/ping", methods=["POST"])
def ping_source(sid):
    """Update last_seen for a log source — called by the Watchdog after ingesting new lines."""
    source = LogSource.query.get_or_404(sid)
    source.last_seen = datetime.utcnow()
    source.total_logs += 1
    db.session.commit()
    return jsonify(source.to_dict())


@dashboard_bp.route("/chart/alerts")
def chart_alerts():
    """Return hourly alert counts for the last 12 hours for the dashboard chart."""
    from sqlalchemy import func
    from datetime import timedelta
    now    = datetime.utcnow()
    labels = []
    data   = []
    for i in range(11, -1, -1):
        hour_start = now - timedelta(hours=i + 1)
        hour_end   = now - timedelta(hours=i)
        count = Alert.query.filter(
            Alert.created_at >= hour_start,
            Alert.created_at < hour_end,
        ).count()
        labels.append(hour_start.strftime("%H:00") if i % 2 == 0 else "")
        data.append(count)
    return jsonify({"labels": labels, "data": data})


@dashboard_bp.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
