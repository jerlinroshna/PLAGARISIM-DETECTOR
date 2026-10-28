from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
from werkzeug.security import check_password_hash
import database

def authenticate_user(username, password):
    """Verifies credentials against the database. Returns user row if valid, else None."""
    conn = database.get_db_connection()
    user = conn.execute(
        "SELECT id, username, password_hash, full_name, role, email FROM users WHERE username = ?",
        (username.strip(),)
    ).fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        return user
    return None

def login_user(user):
    """Establishes user session."""
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]
    session["role"] = user["role"]
    session["email"] = user["email"]
    session.permanent = True

def logout_user():
    """Clears user session."""
    session.clear()

def get_current_user():
    """Returns the currently logged-in user dict from session, or None."""
    if "user_id" in session:
        return {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "role": session.get("role"),
            "email": session.get("email")
        }
    return None

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_current_user() is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if user["role"] not in allowed_roles:
                flash("Access denied: You do not have permission to view this page.", "danger")
                if user["role"] == "student":
                    return redirect(url_for("student.dashboard"))
                else:
                    return redirect(url_for("faculty.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
