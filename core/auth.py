from functools import wraps
from flask import session, redirect, url_for, flash, abort

def login_Required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_Required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Access Denied")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def require_Video_Access(video):
    if not video:
        abort(404)
    allowed_roles = video.get("allowed_roles", [])

    if not allowed_roles:
        return
    
    user_role = session.get("role")
    if user_role not in allowed_roles:
        abort(404)