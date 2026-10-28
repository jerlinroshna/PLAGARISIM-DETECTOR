from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth import authenticate_user, login_user, logout_user, get_current_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    user = get_current_user()
    if user:
        if user["role"] == "faculty":
            return redirect(url_for("faculty.dashboard"))
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    user = get_current_user()
    if user:
        if user["role"] == "faculty":
            return redirect(url_for("faculty.dashboard"))
        return redirect(url_for("student.dashboard"))

    selected_role = request.args.get("role", "student")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("auth/login.html", role=role)

        auth_user = authenticate_user(username, password)
        if not auth_user:
            flash("Invalid username or password. Please verify your credentials.", "danger")
            return render_template("auth/login.html", role=role)

        if auth_user["role"] != role:
            flash(
                f"Role mismatch: '{username}' is registered as a {auth_user['role'].title()}, not as a {role.title()}.",
                "warning"
            )
            return render_template("auth/login.html", role=role)

        login_user(auth_user)
        flash(f"Welcome back, {auth_user['full_name']}!", "success")

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)

        if auth_user["role"] == "faculty":
            return redirect(url_for("faculty.dashboard"))
        else:
            return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html", role=selected_role)

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("auth.login"))
