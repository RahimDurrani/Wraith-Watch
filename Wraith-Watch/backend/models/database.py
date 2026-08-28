
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer,     primary_key=True)
    username = db.Column(db.String(64),  unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20),  default="analyst", nullable=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)
    last_login = db.Column(db.DateTime,    nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LogEntry(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer,     primary_key=True)
    source_ip = db.Column(db.String(45),  nullable=True,  index=True)
    timestamp = db.Column(db.DateTime,    nullable=True,  index=True)
    log_type = db.Column(db.String(20),  nullable=False, index=True)  
    raw_message = db.Column(db.Text,        nullable=False)
    hostname = db.Column(db.String(100), nullable=True)
    event_id = db.Column(db.String(10),  nullable=True,  index=True)  
    source_name = db.Column(db.String(200), nullable=True,  index=True)
    ingested_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "source_ip": self.source_ip,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "log_type": self.log_type,
            "raw_message": self.raw_message,
            "hostname": self.hostname,
            "event_id": self.event_id,
            "source_name": self.source_name,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
        }


class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer,     primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    severity = db.Column(db.String(20),  nullable=False, index=True)
    severity_score = db.Column(db.Integer,     default=0,      index=True)
    rule_name = db.Column(db.String(100), nullable=True)
    source_ip = db.Column(db.String(45),  nullable=True,  index=True)
    log_type = db.Column(db.String(20),  nullable=True)
    status = db.Column(db.String(20),  default="open", index=True)
   
    abuse_score = db.Column(db.Integer,     nullable=True)
    abuse_country = db.Column(db.String(5),   nullable=True)
    abuse_checked = db.Column(db.Boolean,     default=False)
    log_id = db.Column(db.Integer,     db.ForeignKey("logs.id"), nullable=True)
    incident_id = db.Column(db.Integer,     db.ForeignKey("incidents.id"), nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow, index=True)

    SEVERITY_MAP = {"info": 1, "low": 2, "medium": 3, "high": 4, "critical": 5}

    @staticmethod
    def score_for(severity: str) -> int:
        return Alert.SEVERITY_MAP.get(severity, 0)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "severity_score":self.severity_score,
            "rule_name": self.rule_name,
            "rule": self.rule_name,
            "source_ip": self.source_ip,
            "log_type": self.log_type,
            "status": self.status,
            "abuse_score": self.abuse_score,
            "abuse_country": self.abuse_country,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Incident(db.Model):
    __tablename__ = "incidents"
    id = db.Column(db.Integer,     primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    severity = db.Column(db.String(20),  default="medium", nullable=False)
    status = db.Column(db.String(30),  default="new",    nullable=False, index=True)
  
    analyst = db.Column(db.String(64),  nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime,    nullable=True)

    notes = db.relationship("IncidentNote",  back_populates="incident",
                                     cascade="all, delete-orphan",
                                     order_by="IncidentNote.created_at")
    audit_trail = db.relationship("IncidentAudit", back_populates="incident",
                                     cascade="all, delete-orphan",
                                     order_by="IncidentAudit.created_at")
    alerts = db.relationship("Alert", backref="incident_ref",
                                     foreign_keys=[Alert.incident_id],
                                     lazy="dynamic")

    STATUS_FLOW = ["new", "triaged", "investigating", "closed"]

    def next_status(self):
        try:
            idx = self.STATUS_FLOW.index(self.status)
            return self.STATUS_FLOW[idx + 1] if idx + 1 < len(self.STATUS_FLOW) else None
        except ValueError:
            return None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "analyst": self.analyst,
            "alert_ids": [a.id for a in self.alerts],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": [n.to_dict() for n in self.notes],
            "audit": [a.to_dict() for a in self.audit_trail],
        }


class IncidentNote(db.Model):
    __tablename__ = "incident_notes"
    id = db.Column(db.Integer,  primary_key=True)
    content = db.Column(db.Text,     nullable=False)
    incident_id = db.Column(db.Integer,  db.ForeignKey("incidents.id"), nullable=False)
    author = db.Column(db.String(64), nullable=False, default="analyst")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    incident = db.relationship("Incident", back_populates="notes")

    def to_dict(self):
        return {
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IncidentAudit(db.Model):
    """Immutable audit trail — every status change and note is recorded here."""
    __tablename__ = "incident_audit"
    id = db.Column(db.Integer,     primary_key=True)
    incident_id = db.Column(db.Integer,     db.ForeignKey("incidents.id"), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    user = db.Column(db.String(64),  nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    incident = db.relationship("Incident", back_populates="audit_trail")

    def to_dict(self):
        return {
            "action": self.action,
            "user": self.user,
            "time": self.created_at.strftime("%H:%M") if self.created_at else "",
        }


class LogSource(db.Model):
    __tablename__ = "log_sources"
    id = db.Column(db.Integer,     primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    source_type = db.Column(db.String(20),  nullable=False)   
    hostname = db.Column(db.String(100), nullable=True)
    last_seen = db.Column(db.DateTime,    nullable=True, index=True)
    total_logs = db.Column(db.Integer,     default=0)
    is_active = db.Column(db.Boolean,     default=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def health_status(self, stale_minutes: int = 5) -> str:
        if not self.last_seen:
            return "silent"
        from datetime import timedelta
        age = datetime.utcnow() - self.last_seen
        if age <= timedelta(minutes=stale_minutes):
            return "active"
        if age <= timedelta(minutes=stale_minutes * 6):
            return "stale"
        return "silent"

    def minutes_since_seen(self) -> int | None:
        if not self.last_seen:
            return None
        return int((datetime.utcnow() - self.last_seen).total_seconds() / 60)

    def to_dict(self):
        status = self.health_status()
        mins = self.minutes_since_seen()
        return {
            "id": self.id,
            "name": self.name,
            "type": self.source_type,
            "hostname": self.hostname,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "status": status,
            "total_logs": self.total_logs,
            "minutes_ago": mins if mins is not None else 0,
        }


class DetectionRule(db.Model):
    __tablename__ = "detection_rules"
    id = db.Column(db.Integer,     primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text,        nullable=True)
    pattern = db.Column(db.Text,        nullable=False)   
    log_type = db.Column(db.String(20),  nullable=True)    
    severity = db.Column(db.String(20),  nullable=False, default="medium")
    threshold = db.Column(db.Integer,     nullable=True)    
    window_seconds = db.Column(db.Integer,     nullable=True)    
    is_enabled = db.Column(db.Boolean,     default=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern": self.pattern,
            "log_type": self.log_type,
            "severity": self.severity,
            "threshold": self.threshold,
            "window_seconds": self.window_seconds,
            "is_enabled": self.is_enabled,
        }
