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

@faculty_bp.route("/reports")
@login_required
@role_required("faculty")
def reports():
    user = get_current_user()
    conn = database.get_db_connection()

    filter_asgn = request.args.get("assignment", "").strip()
    filter_lang = request.args.get("language", "").strip()
    filter_status = request.args.get("review_status", "").strip()

    # Metrics summary
    total_analyzed = conn.execute("SELECT COUNT(*) FROM analysis_results").fetchone()[0]
    high_count = conn.execute("SELECT COUNT(*) FROM analysis_results WHERE similarity_label = 'High Similarity'").fetchone()[0]
    medium_count = conn.execute("SELECT COUNT(*) FROM analysis_results WHERE similarity_label = 'Medium Similarity'").fetchone()[0]
    low_count = conn.execute("SELECT COUNT(*) FROM analysis_results WHERE similarity_label = 'Low Similarity'").fetchone()[0]
    reviewed_count = conn.execute("SELECT COUNT(*) FROM faculty_reviews WHERE review_status IN ('Reviewed', 'No Concern Identified')").fetchone()[0]
    investigation_count = conn.execute("SELECT COUNT(*) FROM faculty_reviews WHERE review_status = 'Further Investigation Required'").fetchone()[0]

    # Filtered records
    query = """
        SELECT s.id, s.title, s.programming_language, s.submitted_at,
               u.username, u.full_name,
               a.title AS assignment_title, a.subject,
               r.text_similarity_score, r.ast_similarity_score, r.combined_similarity_score,
               r.similarity_label,
               h.academic_year AS hist_year, h.source_filename AS hist_filename,
               f.review_status, f.review_notes
        FROM student_submissions s
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN historical_submissions h ON r.matched_historical_id = h.id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE r.id IS NOT NULL
    """
    params = []

    if filter_asgn:
        query += " AND s.assignment_id = ?"
        params.append(filter_asgn)

    if filter_lang:
        query += " AND LOWER(s.programming_language) = ?"
        params.append(filter_lang.lower())

    if filter_status:
        query += " AND f.review_status = ?"
        params.append(filter_status)

    query += " ORDER BY r.combined_similarity_score DESC, s.submitted_at DESC"

    records = conn.execute(query, params).fetchall()
    assignments = conn.execute("SELECT id, title FROM assignments ORDER BY title").fetchall()
    conn.close()

    return render_template(
        "faculty/reports.html",
        user=user,
        records=records,
        assignments=assignments,
        filter_asgn=filter_asgn,
        filter_lang=filter_lang,
        filter_status=filter_status,
        total_analyzed=total_analyzed,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        reviewed_count=reviewed_count,
        investigation_count=investigation_count
    )

@faculty_bp.route("/reports/export")
@login_required
@role_required("faculty")
def export_csv_report():
    conn = database.get_db_connection()
    records = conn.execute("""
        SELECT s.id AS submission_id, u.username, u.full_name,
               a.title AS assignment_title, a.subject, s.programming_language,
               s.submitted_at,
               h.academic_year AS historical_academic_year,
               h.source_filename AS historical_filename,
               r.text_similarity_score, r.ast_similarity_score, r.combined_similarity_score,
               r.similarity_label,
               f.review_status, f.review_notes, f.reviewed_at
        FROM student_submissions s
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN historical_submissions h ON r.matched_historical_id = h.id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        ORDER BY r.combined_similarity_score DESC
    """).fetchall()
    conn.close()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow([
        "Submission ID", "Student Username", "Student Name", "Assignment", "Subject",
        "Language", "Submission Date", "Historical Year", "Historical File",
        "Text Score (%)", "AST Score (%)", "Combined Score (%)", "Similarity Label",
        "Faculty Review Status", "Faculty Review Notes", "Reviewed At"
    ])

    for row in records:
        writer.writerow([
            row["submission_id"],
            row["username"],
            row["full_name"],
            row["assignment_title"],
            row["subject"],
            row["programming_language"],
            row["submitted_at"],
            row["historical_academic_year"] or "N/A",
            row["historical_filename"] or "None",
            row["text_similarity_score"] or 0.0,
            row["ast_similarity_score"] or 0.0,
            row["combined_similarity_score"] or 0.0,
            row["similarity_label"] or "N/A",
            row["review_status"] or "Pending Review",
            row["review_notes"] or "",
            row["reviewed_at"] or ""
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=plagiarism_analysis_report.csv"}
    )

@faculty_bp.route("/demo_accounts")
@login_required
@role_required("faculty")
def demo_accounts():
    conn = database.get_db_connection()
    students = conn.execute("SELECT username, full_name, role, email FROM users WHERE role = 'student' ORDER BY username").fetchall()
    faculty = conn.execute("SELECT username, full_name, role, email FROM users WHERE role = 'faculty' ORDER BY username").fetchall()
    conn.close()

    return render_template(
        "faculty/demo_accounts.html",
        user=get_current_user(),
        students=students,
        faculty=faculty
    )

@faculty_bp.route("/demo_accounts/download")
@login_required
@role_required("faculty")
def download_demo_accounts_csv():
    if os.path.exists(config.DEMO_ACCOUNTS_CSV):
        return send_file(
            config.DEMO_ACCOUNTS_CSV,
            mimetype="text/csv",
            as_attachment=True,
            download_name="demo_accounts.csv"
        )
    flash("Demo accounts CSV not found.", "warning")
    return redirect(url_for("faculty.demo_accounts"))

@faculty_bp.route("/profile")
@login_required
@role_required("faculty")
def profile():
    user = get_current_user()
    conn = database.get_db_connection()
    assignments_created = conn.execute("SELECT COUNT(*) FROM assignments WHERE created_by = ?", (user["id"],)).fetchone()[0]
    hist_uploaded = conn.execute("SELECT COUNT(*) FROM historical_submissions WHERE uploaded_by = ?", (user["id"],)).fetchone()[0]
    reviews_done = conn.execute("SELECT COUNT(*) FROM faculty_reviews WHERE faculty_id = ?", (user["id"],)).fetchone()[0]
    conn.close()

    return render_template(
        "faculty/profile.html",
        user=user,
        assignments_created=assignments_created,
        hist_uploaded=hist_uploaded,
        reviews_done=reviews_done
    )
