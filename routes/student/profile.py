import os
import csv
import io
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import (
    render_template, request, redirect, url_for, flash, 
    abort, Response, send_file, jsonify
)
from auth import login_required, role_required, get_current_user
import config
import database
from analyzers.comparator import CodeComparator
from routes.student import student_bp, SUPPORTED_ANALYSIS_LANGUAGES

@student_bp.route("/profile")
@login_required
@role_required("student")
def profile():
    user = get_current_user()
    conn = database.get_db_connection()

    stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN analysis_status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN analysis_status = 'pending' THEN 1 ELSE 0 END) as pending
        FROM student_submissions
        WHERE student_id = ?
    """, (user["id"],)).fetchone()

    languages_used = conn.execute("""
        SELECT DISTINCT programming_language FROM student_submissions WHERE student_id = ?
    """, (user["id"],)).fetchall()

    conn.close()

    return render_template(
        "student/profile.html",
        user=user,
        stats=stats,
        languages_used=[l[0].upper() for l in languages_used]
    )
