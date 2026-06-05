from functools import wraps
from flask import session, redirect, url_for, flash

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