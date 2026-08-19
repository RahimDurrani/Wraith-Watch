

from flask           import Blueprint, request, jsonify
from datetime        import datetime
from models.database import db, User
from utils.auth      import bcrypt, generate_token, login_required, validate_signup

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email    = (data.get("email")    or "").strip()
    password =  data.get("password") or ""

    error = validate_signup(username, email, password)
    if error:
        return jsonify({"error": error}), 400

    user = User(
        username      = username,
        email         = email,
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8"),
        role          = "analyst",
    )
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.to_dict())
    return jsonify({
        "success": True,
        "token":   token,
        "user":    user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data       = request.get_json(silent=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password   =  data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "Username/email and password are required."}), 400

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Incorrect username/email or password."}), 401

    user.last_login = datetime.utcnow()
    db.session.commit()

    token = generate_token(user.to_dict())
    return jsonify({
        "success": True,
        "token":   token,
        "user":    user.to_dict(),
    })


@auth_bp.route("/me")
@login_required
def me():
    user = User.query.get(request.user["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())
