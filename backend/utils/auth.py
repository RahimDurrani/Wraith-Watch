# backend/utils/auth.py
# ─────────────────────────────────────────────────────────
# JWT helpers, login_required decorator, validation.
# ─────────────────────────────────────────────────────────

import re
import jwt
from datetime  import datetime, timedelta
from functools import wraps
from flask     import request, jsonify
from flask_bcrypt import Bcrypt

bcrypt     = Bcrypt()
SECRET_KEY = "dev-secret-key-change-in-production-abc123xyz"
TOKEN_EXPIRY_HOURS = 24
EMAIL_RE   = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def generate_token(user_dict: dict) -> str:
    payload = {
        "user_id":  user_dict["id"],
        "username": user_dict["username"],
        "role":     user_dict["role"],
        "exp":      datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        payload = decode_token(auth_header.split(" ", 1)[1])
        if not payload:
            return jsonify({"error": "Token expired or invalid"}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated


def validate_signup(username: str, email: str, password: str) -> str | None:
    from models.database import User
    if not username or len(username.strip()) < 3:
        return "Username must be at least 3 characters."
    if not EMAIL_RE.match(email or ""):
        return "Enter a valid email address."
    if not password or len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number."
    if User.query.filter_by(username=username.strip()).first():
        return "That username is already taken."
    if User.query.filter_by(email=email.strip()).first():
        return "An account with that email already exists."
    return None
