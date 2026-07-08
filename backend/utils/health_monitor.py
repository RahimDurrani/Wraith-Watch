# backend/utils/health_monitor.py
# ─────────────────────────────────────────────────────────
# Week 5 deliverable: background scheduler that checks log
# source health every 60 seconds.
#
# Uses the `schedule` library — simpler than Celery for a
# 12-week project. Runs in a daemon thread so it dies
# cleanly when Flask exits.
#
# What it does:
#   - Reads all LogSource records from the DB
#   - Checks last_seen timestamp against stale threshold
#   - Updates status in DB (active / stale / silent)
#   - Logs a warning if a source goes silent
# ─────────────────────────────────────────────────────────

import threading
import logging
import schedule
import time
from datetime import datetime, timedelta

logger = logging.getLogger("wraithwatch.health_monitor")


def _check_sources(app):
    """
    Check all log sources and update their health status.
    Runs inside the Flask app context so it can access the DB.
    """
    with app.app_context():
        from models.database import db, LogSource

        sources = LogSource.query.filter_by(is_active=True).all()
        stale_minutes = app.config.get("STALE_SOURCE_MINUTES", 5)

        for source in sources:
            old_status = source.health_status(stale_minutes)

            if old_status == "silent":
                logger.warning(
                    f"Log source '{source.name}' ({source.hostname}) is SILENT — "
                    f"last seen {source.minutes_since_seen()} minutes ago."
                )
            elif old_status == "stale":
                logger.info(
                    f"Log source '{source.name}' is stale — "
                    f"last seen {source.minutes_since_seen()} minutes ago."
                )

        db.session.commit()


def _run_scheduler():
    """Background thread — runs the schedule loop forever."""
    while True:
        schedule.run_pending()
        time.sleep(10)


def start(app):
    """
    Start the health monitor background scheduler.
    Call once from app.py after the app is created.

    Args:
        app - Flask app instance
    """
    # Schedule a check every 60 seconds
    schedule.every(60).seconds.do(_check_sources, app=app)

    # Run immediately on startup so status is current from the start
    _check_sources(app)

    # Start the background thread
    t = threading.Thread(target=_run_scheduler, daemon=True, name="health-monitor")
    t.start()
    logger.info("Health monitor started — checking every 60 seconds.")


def seed_log_sources(app):
    """
    Seed the DB with demo log sources on first run.
    Only adds sources if the table is empty.
    """
    with app.app_context():
        from models.database import db, LogSource

        if LogSource.query.count() > 0:
            return   # Already seeded

        sources = [
            LogSource(name="apache-access.log", source_type="apache",
                      hostname="web01",        last_seen=datetime.utcnow(),
                      total_logs=4821),
            LogSource(name="auth.log",          source_type="syslog",
                      hostname="web01",        last_seen=datetime.utcnow() - timedelta(seconds=45),
                      total_logs=2341),
            LogSource(name="Security.evtx",     source_type="evtx",
                      hostname="DESKTOP-WIN10", last_seen=datetime.utcnow() - timedelta(minutes=8),
                      total_logs=892),
            LogSource(name="syslog",            source_type="syslog",
                      hostname="web01",        last_seen=datetime.utcnow() - timedelta(minutes=2),
                      total_logs=1203),
            LogSource(name="System.evtx",       source_type="evtx",
                      hostname="FINANCE-PC",   last_seen=datetime.utcnow() - timedelta(hours=2),
                      total_logs=341),
        ]
        db.session.add_all(sources)
        db.session.commit()
        logger.info(f"Seeded {len(sources)} log sources.")
