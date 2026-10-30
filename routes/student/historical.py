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

@student_bp.route("/historical")
@login_required
@role_required("student")
def historical():
    user = get_current_user()
    conn = database.get_db_connection()

    filter_year = request.args.get("year", "").strip()
    filter_lang = request.args.get("language", "").strip()
    search_q = request.args.get("search", "").strip()

    # Strict data isolation: students see ONLY their own authorized historical submissions
    query = """
        SELECT id, student_id, academic_year, subject, assignment_name, programming_language,
               source_filename, source_code, batch_label, created_at
        FROM historical_submissions
        WHERE is_authorized_for_students = 1
          AND (student_id = ? OR student_id = ? OR (? = 'demo_student' AND student_id IN ('STU001', 'demo_student', 'DEMO-HIST-STU1')))
    """
    params = [user["username"], str(user["id"]), user["username"]]

    if filter_year:
        query += " AND academic_year = ?"
        params.append(filter_year)

    if filter_lang:
        query += " AND LOWER(programming_language) = ?"
        params.append(filter_lang.lower())

    if search_q:
        query += " AND (assignment_name LIKE ? OR subject LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

    query += " ORDER BY academic_year DESC, created_at DESC"

    records = conn.execute(query, params).fetchall()

    years = conn.execute("""
        SELECT DISTINCT academic_year FROM historical_submissions
        WHERE is_authorized_for_students = 1
          AND (student_id = ? OR student_id = ? OR (? = 'demo_student' AND student_id IN ('STU001', 'demo_student', 'DEMO-HIST-STU1')))
        ORDER BY academic_year DESC
    """, (user["username"], str(user["id"]), user["username"])).fetchall()

    subjects = conn.execute("""
        SELECT DISTINCT subject FROM historical_submissions
        WHERE is_authorized_for_students = 1
          AND (student_id = ? OR student_id = ? OR (? = 'demo_student' AND student_id IN ('STU001', 'demo_student', 'DEMO-HIST-STU1')))
        ORDER BY subject
    """, (user["username"], str(user["id"]), user["username"])).fetchall()

    conn.close()

    return render_template(
        "student/historical.html",
        user=user,
        records=records,
        years=years,
        subjects=subjects,
        filter_year=filter_year,
        filter_lang=filter_lang,
        search_q=search_q,
        languages=config.LANGUAGE_DISPLAY_NAMES
    )
