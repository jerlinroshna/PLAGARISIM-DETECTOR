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

@faculty_bp.route("/submissions")
@login_required
@role_required("faculty")
def submissions():
    user = get_current_user()
    conn = database.get_db_connection()

    # Filters
    search_user = request.args.get("search", "").strip()
    filter_asgn = request.args.get("assignment", "").strip()
    filter_lang = request.args.get("language", "").strip()
    filter_label = request.args.get("similarity", "").strip()
    filter_review = request.args.get("review", "").strip()

    query = """
        SELECT s.id, s.title, s.programming_language, s.source_filename, s.submitted_at, s.analysis_status,
               u.username, u.full_name,
               a.id AS assignment_id, a.title AS assignment_title, a.subject,
               r.id AS result_id, r.text_similarity_score, r.ast_similarity_score,
               r.combined_similarity_score, r.similarity_label,
               f.review_status
        FROM student_submissions s
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE 1=1
    """
    params = []

    if search_user:
        query += " AND (u.username LIKE ? OR u.full_name LIKE ?)"
        params.extend([f"%{search_user}%", f"%{search_user}%"])

    if filter_asgn:
        query += " AND s.assignment_id = ?"
        params.append(filter_asgn)

    if filter_lang:
        query += " AND LOWER(s.programming_language) = ?"
        params.append(filter_lang.lower())

    if filter_label:
        query += " AND r.similarity_label = ?"
        params.append(filter_label)

    if filter_review:
        query += " AND f.review_status = ?"
        params.append(filter_review)

    query += " ORDER BY s.submitted_at DESC"

    all_subs = conn.execute(query, params).fetchall()

    assignments_list = conn.execute("SELECT id, title FROM assignments ORDER BY title").fetchall()
    conn.close()

    return render_template(
        "faculty/submissions.html",
        user=user,
        submissions=all_subs,
        assignments=assignments_list,
        search_user=search_user,
        filter_asgn=filter_asgn,
        filter_lang=filter_lang,
        filter_label=filter_label,
        filter_review=filter_review
    )

@faculty_bp.route("/submit", methods=["GET", "POST"])
@login_required
@role_required("faculty")
def submit():
    """Faculty code submission is permanently disabled per institutional role policy."""
    if request.is_json or request.headers.get("Accept") == "application/json":
        return {"error": "Forbidden", "message": "Faculty code submissions are disabled. Plagiarism screening is restricted to students."}, 403
    flash("Faculty code submissions are disabled. Code submissions are restricted to students.", "warning")
    return abort(403)

@faculty_bp.route("/analysis/<int:sub_id>")
@login_required
@role_required("faculty")
def analysis_detail(sub_id):
    conn = database.get_db_connection()

    sub = conn.execute("""
        SELECT s.id, s.title, s.programming_language, s.source_filename, s.source_code,
               s.submitted_at, s.analysis_status,
               u.id AS student_id, u.username AS student_username, u.full_name AS student_name,
               a.id AS assignment_id, a.title AS assignment_title, a.subject
        FROM student_submissions s
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        WHERE s.id = ?
    """, (sub_id,)).fetchone()

    if not sub:
        conn.close()
        flash("Submission not found.", "warning")
        return redirect(url_for("faculty.submissions"))

    result = conn.execute("""
        SELECT r.id, r.matched_historical_id, r.text_similarity_score, r.ast_similarity_score,
               r.combined_similarity_score, r.similarity_label, r.analysis_summary, r.analyzed_at,
               r.grok_explanation, r.grok_explained_at,
               h.academic_year, h.subject AS hist_subject, h.assignment_name AS hist_assignment,
               h.programming_language AS hist_language, h.source_filename AS hist_filename,
               h.source_code AS hist_source_code, h.batch_label AS hist_batch
        FROM analysis_results r
        LEFT JOIN historical_submissions h ON r.matched_historical_id = h.id
        WHERE r.submission_id = ?
    """, (sub_id,)).fetchone()

    # Re-run analysis if missing or requested
    if not result:
        conn.close()
        CodeComparator.analyze_submission(sub_id)
        return redirect(url_for("faculty.analysis_detail", sub_id=sub_id))

    # Matched evidence line intervals
    evidence_rows = conn.execute("""
        SELECT student_code_lines, historical_code_lines, details
        FROM matched_evidence
        WHERE analysis_result_id = ?
    """, (result["id"],)).fetchall()

    student_matched_lines = []
    historical_matched_lines = []
    matching_spans = []

    for ev in evidence_rows:
        if ev["student_code_lines"]:
            try:
                ranges = json.loads(ev["student_code_lines"])
                for r_start, r_end in ranges:
                    student_matched_lines.extend(range(r_start, r_end + 1))
            except Exception:
                pass
        if ev["historical_code_lines"]:
            try:
                ranges = json.loads(ev["historical_code_lines"])
                for r_start, r_end in ranges:
                    historical_matched_lines.extend(range(r_start, r_end + 1))
            except Exception:
                pass
        if ev["details"]:
            try:
                matching_spans = json.loads(ev["details"])
            except Exception:
                pass

    review = conn.execute("""
        SELECT r.id, r.review_status, r.review_notes, r.reviewed_at,
               u.full_name AS reviewer_name
        FROM faculty_reviews r
        LEFT JOIN users u ON r.faculty_id = u.id
        WHERE r.analysis_result_id = ?
    """, (result["id"],)).fetchone()

    conn.close()

    # Line formatting for side-by-side view
    student_lines = sub["source_code"].splitlines()
    hist_lines = result["hist_source_code"].splitlines() if result["hist_source_code"] else []

    return render_template(
        "faculty/comparison.html",
        user=get_current_user(),
        sub=sub,
        result=result,
        review=review,
        student_lines=student_lines,
        hist_lines=hist_lines,
        student_matched_lines=set(student_matched_lines),
        historical_matched_lines=set(historical_matched_lines),
        matching_spans=matching_spans
    )

@faculty_bp.route("/review/<int:sub_id>", methods=["POST"])
@login_required
@role_required("faculty")
def save_review(sub_id):
    user = get_current_user()
    conn = database.get_db_connection()

    review_status = request.form.get("review_status", "Pending Review")
    review_notes = request.form.get("review_notes", "").strip()

    result_row = conn.execute(
        "SELECT id FROM analysis_results WHERE submission_id = ?",
        (sub_id,)
    ).fetchone()

    if not result_row:
        conn.close()
        flash("Analysis result not found for this submission.", "danger")
        return redirect(url_for("faculty.submissions"))

    conn.execute("""
        INSERT OR REPLACE INTO faculty_reviews 
        (analysis_result_id, faculty_id, review_status, review_notes, reviewed_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (result_row["id"], user["id"], review_status, review_notes))
    conn.commit()
    conn.close()

    flash(f"Faculty review updated: Status set to '{review_status}'.", "success")
    return redirect(url_for("faculty.analysis_detail", sub_id=sub_id))
