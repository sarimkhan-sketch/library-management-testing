"""Registration, login/logout and the access-control decorators."""
import secrets
import sqlite3
from functools import wraps

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .validators import check_password, check_username

bp = Blueprint("auth", __name__, url_prefix="/auth")


def error(message, status):
    return jsonify({"error": message}), status


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return error("login required", 401)
        user = get_db().execute(
            "SELECT users.* FROM tokens JOIN users ON users.id = tokens.user_id WHERE token = ?",
            (header[len("Bearer "):],),
        ).fetchone()
        if user is None:
            return error("invalid or expired token", 401)
        g.user = user
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user["role"] != "admin":
            return error("admin access required", 403)
        return view(*args, **kwargs)
    return wrapped


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username, password = data.get("username"), data.get("password")
    problem = check_username(username) or check_password(password)
    if problem:
        return error(problem, 400)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'member')",
            (username, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("username already taken", 409)
    return jsonify({"id": cur.lastrowid, "username": username, "role": "member"}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = get_db().execute(
        "SELECT * FROM users WHERE username = ?", (data.get("username"),)
    ).fetchone()
    if user is None or not check_password_hash(user["password_hash"], str(data.get("password", ""))):
        return error("invalid username or password", 401)
    token = secrets.token_hex(32)
    db = get_db()
    db.execute("INSERT INTO tokens (token, user_id) VALUES (?, ?)", (token, user["id"]))
    db.commit()
    return jsonify({"token": token, "role": user["role"]})


@bp.post("/logout")
@login_required
def logout():
    token = request.headers["Authorization"][len("Bearer "):]
    db = get_db()
    db.execute("DELETE FROM tokens WHERE token = ?", (token,))
    db.commit()
    return jsonify({"message": "logged out"})
