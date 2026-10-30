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

    # Flagged submissions exceeding 70% threshold
    flagged_submissions = conn.execute("""
        SELECT s.id, s.title, s.programming_language, s.submitted_at,
               u.username, u.full_name,
               a.title AS assignment_title,
               r.combined_similarity_score, r.similarity_label,
               f.review_status
        FROM student_submissions s
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE r.combined_similarity_score >= 70
        ORDER BY r.combined_similarity_score DESC
        LIMIT 6
    """).fetchall()

    # Similarity score distribution across all evaluated results
    dist_stats = conn.execute("""
        SELECT 
            SUM(CASE WHEN combined_similarity_score < 30 THEN 1 ELSE 0 END) AS low_count,
            SUM(CASE WHEN combined_similarity_score >= 30 AND combined_similarity_score < 70 THEN 1 ELSE 0 END) AS med_count,
            SUM(CASE WHEN combined_similarity_score >= 70 THEN 1 ELSE 0 END) AS high_count,
            COUNT(*) AS total_count
        FROM analysis_results
    """).fetchone()

    dist_low = dist_stats["low_count"] if dist_stats and dist_stats["low_count"] is not None else 0
    dist_med = dist_stats["med_count"] if dist_stats and dist_stats["med_count"] is not None else 0
    dist_high = dist_stats["high_count"] if dist_stats and dist_stats["high_count"] is not None else 0
    dist_total = dist_stats["total_count"] if dist_stats and dist_stats["total_count"] is not None else 0

    # Active assignments with upcoming deadlines & submission ratios
    raw_deadlines = conn.execute("""
        SELECT a.id, a.title, a.subject, a.deadline,
               (SELECT COUNT(*) FROM student_submissions s WHERE s.assignment_id = a.id) AS submission_count
        FROM assignments a
        WHERE a.is_active = 1 AND a.deadline IS NOT NULL AND a.deadline != ''
        ORDER BY a.deadline ASC
        LIMIT 4
    """).fetchall()

    now = datetime.now()
    upcoming_deadlines = []
    for d in raw_deadlines:
        d_dict = dict(d)
        deadline_str = d_dict.get("deadline")
        time_left_text = "Active"
        is_urgent = False
        display_date = "No deadline"
        if deadline_str:
            try:
                dt = datetime.strptime(deadline_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                display_date = dt.strftime("%b %d, %H:%M")
                diff = dt - now
                if diff.total_seconds() < 0:
                    time_left_text = "Closed"
                elif diff.days == 0:
                    hours = int(diff.total_seconds() // 3600)
                    time_left_text = f"In {max(1, hours)}h"
                    is_urgent = True
                elif diff.days == 1:
                    time_left_text = "Tomorrow"
                    is_urgent = True
                elif diff.days <= 3:
                    time_left_text = f"In {diff.days} days"
                    is_urgent = True
                else:
                    time_left_text = f"In {diff.days} days"
            except Exception:
                display_date = deadline_str
        
        sub_cnt = d_dict.get("submission_count", 0)
        sub_pct = int(round((sub_cnt / total_students * 100))) if total_students > 0 else 0
        d_dict["display_date"] = display_date
        d_dict["time_left_text"] = time_left_text
        d_dict["is_urgent"] = is_urgent
        d_dict["sub_ratio"] = f"{sub_cnt}/{total_students}"
        d_dict["sub_pct"] = min(100, sub_pct)
        upcoming_deadlines.append(d_dict)

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
        recent_submissions=recent_submissions,
        flagged_submissions=flagged_submissions,
        dist_low=dist_low,
        dist_med=dist_med,
        dist_high=dist_high,
        dist_total=dist_total,
        upcoming_deadlines=upcoming_deadlines
    )
