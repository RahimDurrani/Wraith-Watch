import json
import time
from flask       import Blueprint, request, jsonify, Response
from utils.log_generator import LIVE_LOG_BUFFER, LOG_LOCK

live_logs_bp = Blueprint("live_logs", __name__, url_prefix="/api/logs")


@live_logs_bp.route("/recent")
def logs_recent():
    """
    Polling endpoint — React calls this every 2s with
    ?since=<last_id> and receives only new log lines.

    Query params:
      since     - return only entries with id > since (default 0)
      limit     - max rows returned (default 100)
      log_type  - filter by 'apache' | 'syslog' | 'evtx'
      flagged   - 'true' to show only flagged entries
      search    - substring search on message / hostname / source
    """
    since    = int(request.args.get("since",    0))
    limit    = int(request.args.get("limit",    100))
    log_type = request.args.get("log_type", "").strip()
    flagged  = request.args.get("flagged",  "").lower() == "true"
    search   = request.args.get("search",   "").lower().strip()

    with LOG_LOCK:
        logs = list(LIVE_LOG_BUFFER)

    # Only entries newer than since
    logs = [l for l in logs if l["id"] > since]

    # Apply filters
    if log_type:
        logs = [l for l in logs if l["log_type"] == log_type]
    if flagged:
        logs = [l for l in logs if l["flagged"]]
    if search:
        logs = [l for l in logs
                if search in l["message"].lower()
                or search in l["hostname"].lower()
                or search in l["source"].lower()]

    logs = logs[-limit:]   # newest N rows

    return jsonify({
        "logs":            logs,
        "last_id":         logs[-1]["id"] if logs else since,
        "total_in_buffer": len(LIVE_LOG_BUFFER),
    })


@live_logs_bp.route("/stream")
def logs_stream():
    """
    Server-Sent Events endpoint — pushes new log lines as
    they arrive. Connect with EventSource in React for true
    real-time streaming without polling.
    """
    def generate():
        last_id = 0
        while True:
            with LOG_LOCK:
                new = [l for l in LIVE_LOG_BUFFER if l["id"] > last_id]
            if new:
                for log in new:
                    yield f"data: {json.dumps(log)}\n\n"
                last_id = new[-1]["id"]
            time.sleep(1.0)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@live_logs_bp.route("/stats")
def logs_stats():
    """Returns count breakdown for the topbar stat pills."""
    with LOG_LOCK:
        logs = list(LIVE_LOG_BUFFER)

    by_type  = {}
    by_level = {"critical": 0, "high": 0, "medium": 0, "info": 0}
    flagged_total = 0

    for l in logs:
        by_type[l["log_type"]] = by_type.get(l["log_type"], 0) + 1
        by_level[l.get("flag_level", "info")] = by_level.get(l.get("flag_level", "info"), 0) + 1
        if l["flagged"]:
            flagged_total += 1

    return jsonify({
        "total":    len(logs),
        "flagged":  flagged_total,
        "by_type":  by_type,
        "by_level": by_level,
    })
