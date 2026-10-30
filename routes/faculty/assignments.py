import os
import csv
import io
import json
from werkzeug.utils import secure_filename
from flask import (
    render_template, request, redirect, url_for, flash, 
    abort, Response, send_file, jsonify
)
from auth import login_required, role_required, get_current_user
import config
import database
from analyzers.comparator import CodeComparator
from services.grok_service import GrokService
from services.report_renderer import render_html_investigation_report
from routes.faculty import faculty_bp

@faculty_bp.route("/assignments", methods=["GET", "POST"])
@login_required
@role_required("faculty")
def assignments():
    user = get_current_user()
    conn = database.get_db_connection()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        deadline = request.form.get("deadline", "").strip()
        langs = request.form.getlist("allowed_languages")

        if not title or not subject:
            flash("Assignment Title and Subject are required.", "danger")
            return redirect(url_for("faculty.assignments"))

        if not langs:
            flash("Please select at least one permitted programming language.", "danger")
            return redirect(url_for("faculty.assignments"))

        allowed_languages_str = ",".join(langs)

        conn.execute("""
            INSERT INTO assignments (title, subject, description, allowed_languages, deadline, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (title, subject, description, allowed_languages_str, deadline, user["id"]))
        conn.commit()
        flash(f"Assignment '{title}' created successfully.", "success")
        conn.close()
        return redirect(url_for("faculty.assignments"))

    all_assignments = conn.execute("""
        SELECT a.id, a.title, a.subject, a.description, a.allowed_languages, 
               a.deadline, a.is_active, a.created_at,
               COUNT(s.id) AS submission_count
        FROM assignments a
        LEFT JOIN student_submissions s ON a.id = s.assignment_id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()

    return render_template(
        "faculty/assignments.html",
        user=user,
        assignments=all_assignments,
        all_languages=config.ALLOWED_EXTENSIONS
    )

@faculty_bp.route("/assignment/<int:asgn_id>/toggle", methods=["POST"])
@login_required
@role_required("faculty")
def toggle_assignment(asgn_id):
    conn = database.get_db_connection()
    asgn = conn.execute("SELECT id, is_active, title FROM assignments WHERE id = ?", (asgn_id,)).fetchone()
    if asgn:
        new_status = 0 if asgn["is_active"] else 1
        conn.execute("UPDATE assignments SET is_active = ? WHERE id = ?", (new_status, asgn_id))
        conn.commit()
        status_label = "enabled" if new_status == 1 else "disabled"
        flash(f"Assignment '{asgn['title']}' has been {status_label}.", "info")
    conn.close()
    return redirect(url_for("faculty.assignments"))
