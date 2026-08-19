import os
import logging
from flask        import Flask
from flask_cors   import CORS
from flask_bcrypt import Bcrypt
from dotenv       import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(name)s — %(message)s")

load_dotenv()

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

bcrypt = Bcrypt(app)

# ── Configuration ─────────────────────────────────────────────────────────────
# SQLite for development — change to PostgreSQL in Week 9:
# DATABASE_URL=postgresql://user:password@localhost:5432/wraithwatch
app.config["SQLALCHEMY_DATABASE_URI"]        = os.environ.get("DATABASE_URL", "sqlite:///wraithwatch.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"]                  = os.environ.get("LOG_UPLOAD_FOLDER", "uploads")
app.config["MAX_CONTENT_LENGTH"]             = 32 * 1024 * 1024   # 32 MB
app.config["STALE_SOURCE_MINUTES"]           = int(os.environ.get("STALE_SOURCE_MINUTES", 5))
app.config["SECRET_KEY"]                     = os.environ.get("SECRET_KEY", "dev-secret-key")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ── Database ──────────────────────────────────────────────────────────────────
from models.database import db
db.init_app(app)

# Share bcrypt with utils.auth
import utils.auth as _auth_module
_auth_module.bcrypt = bcrypt

# ── Register blueprints ───────────────────────────────────────────────────────
from routes.dashboard import dashboard_bp
from routes.auth      import auth_bp
from routes.upload    import upload_bp
from routes.live_logs import live_logs_bp
from routes.reports   import reports_bp
from routes.rules     import rules_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(live_logs_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(rules_bp)

# ── Create tables + seed data ─────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    print("  Database → wraithwatch.db (all tables created)")

    from utils.seeder import seed_all
    seed_all(app, bcrypt)

    from utils.health_monitor import seed_log_sources
    seed_log_sources(app)

    from routes.rules import seed_rules
    seed_rules(app)

# ── Start background services ─────────────────────────────────────────────────
from utils.health_monitor import start as start_health_monitor
start_health_monitor(app)

from utils import log_generator
log_generator.start(app)

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  WraithWatch API  →  http://localhost:5000")
    print("  Database         →  backend/wraithwatch.db")
    print("  Demo login       →  analyst / Password123!\n")
    app.run(debug=False, port=5000)
