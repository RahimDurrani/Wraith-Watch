import time
import bleach
from functools import wraps
from collections import defaultdict
from flask import request, jsonify

def sanitise(text: str) -> str:
    """
    Strip all HTML tags and attributes from user input.
    Returns clean plain text safe to store and render.
    """
    if not text:
        return ""
    return bleach.clean(text, tags=[], attributes={}, strip=True).strip()


# ── Role-based access control ─────────────────────────────────────────────────
# Two roles: 'admin' can do everything; 'analyst' can view and manage
# incidents but cannot delete data or manage users.

def role_required(*allowed_roles):
    """
    Decorator that restricts a route to specific roles.
    Must be used AFTER @login_required so request.user is set.

    Usage:
        @app.route("/api/admin/thing")
        @login_required
        @role_required("admin")
        def admin_only():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = getattr(request, "user", None)
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            if user.get("role") not in allowed_roles:
                return jsonify({
                    "error": "You do not have permission to perform this action.",
                    "required_role": list(allowed_roles),
                }), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ── Login rate limiting ───────────────────────────────────────────────────────
# Simple in-memory rate limiter to slow down brute force attacks against the
# login endpoint. Tracks failed attempts per IP within a time window.

_login_attempts = defaultdict(list)   # { ip: [timestamp, ...] }
MAX_ATTEMPTS   = 5
WINDOW_SECONDS = 300   # 5 minutes


def check_rate_limit(ip: str) -> tuple[bool, int]:
    """
    Check whether an IP has exceeded the login attempt limit.

    Returns:
        (allowed, seconds_until_reset)
        allowed = True if the request may proceed
    """
    now    = time.time()
    cutoff = now - WINDOW_SECONDS
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]

    if len(_login_attempts[ip]) >= MAX_ATTEMPTS:
        oldest = min(_login_attempts[ip])
        return False, int(WINDOW_SECONDS - (now - oldest))
    return True, 0


def record_failed_attempt(ip: str) -> None:
    """Record a failed login attempt for rate limiting."""
    _login_attempts[ip].append(time.time())


def clear_attempts(ip: str) -> None:
    """Clear attempts after a successful login."""
    _login_attempts.pop(ip, None)
