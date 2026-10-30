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
from services.grok_service import GrokService
from services.report_renderer import render_html_investigation_report
from routes.faculty import faculty_bp

@faculty_bp.route("/dashboard")
@login_required
@role_required("faculty")
def dashboard():
    user = get_current_user()
    conn = database.get_db_connection()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'student'"
    ).fetchone()[0]

    total_assignments = conn.execute(
        "SELECT COUNT(*) FROM assignments"
    ).fetchone()[0]

    total_submissions = conn.execute(
        "SELECT COUNT(*) FROM student_submissions"
    ).fetchone()[0]

    analyses_completed = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE analysis_status = 'completed'"
    ).fetchone()[0]

    reviews_required = conn.execute("""
        SELECT COUNT(*) FROM faculty_reviews 
        WHERE review_status = 'Pending Review' OR review_status = 'Further Investigation Required'
    """).fetchone()[0]

    historical_count = conn.execute(
        "SELECT COUNT(*) FROM historical_submissions"
    ).fetchone()[0]

    # Recent submissions table across all students (last 8)
    recent_submissions = conn.execute("""
        SELECT s.id, s.title, s.programming_language, s.submitted_at, s.analysis_status,
               u.username, u.full_name,
               a.title AS assignment_title,
               r.combined_similarity_score, r.similarity_label,
               f.review_status
        FROM student_submissions s
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        ORDER BY s.submitted_at DESC
        LIMIT 8
    """).fetchall()

    conn.close()

    return render_template(
        "faculty/dashboard.html",
        user=user,
        total_students=total_students,
        total_assignments=total_assignments,
        total_submissions=total_submissions,
        analyses_completed=analyses_completed,
        reviews_required=reviews_required,
        historical_count=historical_count,
        recent_submissions=recent_submissions
    )
