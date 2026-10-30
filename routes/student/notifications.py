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
from routes.student import student_bp

@student_bp.route("/notifications")
@login_required
@role_required("student")
def notifications():
    user = get_current_user()
    conn = database.get_db_connection()

    all_notifs = conn.execute("""
        SELECT id, title, message, category, link_url, is_read, created_at
        FROM student_notifications
        WHERE student_id = ?
        ORDER BY created_at DESC
    """, (user["id"],)).fetchall()

    unread_count = conn.execute("""
        SELECT COUNT(*) FROM student_notifications
        WHERE student_id = ? AND is_read = 0
    """, (user["id"],)).fetchone()[0]

    conn.close()

    return render_template(
        "student/notifications.html",
        user=user,
        notifications=all_notifs,
        unread_count=unread_count
    )

@student_bp.route("/notifications/read/<int:notif_id>", methods=["POST"])
@login_required
@role_required("student")
def mark_notification_read(notif_id):
    user = get_current_user()
    conn = database.get_db_connection()
    conn.execute("UPDATE student_notifications SET is_read = 1 WHERE id = ? AND student_id = ?", (notif_id, user["id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("student.notifications"))

@student_bp.route("/notifications/read-all", methods=["POST"])
@login_required
@role_required("student")
def mark_all_notifications_read():
    user = get_current_user()
    conn = database.get_db_connection()
    conn.execute("UPDATE student_notifications SET is_read = 1 WHERE student_id = ?", (user["id"],))
    conn.commit()
    conn.close()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("student.notifications"))

@student_bp.route("/academic-integrity")
@login_required
@role_required("student")
def academic_integrity():
    user = get_current_user()
    return render_template(
        "student/academic_integrity.html",
        user=user
    )
