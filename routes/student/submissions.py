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

@student_bp.route("/submissions")
@login_required
@role_required("student")
def submissions():
    user = get_current_user()
    conn = database.get_db_connection()

    q = request.args.get("q", "").strip()
    filter_asgn = request.args.get("assignment", "").strip()
    filter_lang = request.args.get("language", "").strip()
    filter_status = request.args.get("status", "").strip()
    filter_band = request.args.get("similarity", "").strip()

    # Summary metrics
    total_count = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ?",
        (user["id"],)
    ).fetchone()[0]

    completed_count = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ? AND analysis_status = 'completed'",
        (user["id"],)
    ).fetchone()[0]

    pending_count = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ? AND analysis_status = 'pending'",
        (user["id"],)
    ).fetchone()[0]

    reviewed_count = conn.execute("""
        SELECT COUNT(*) FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ? AND f.review_status IN ('Reviewed', 'No Concern Identified')
    """, (user["id"],)).fetchone()[0]

    query = """
        SELECT s.id, s.title, s.programming_language, s.source_filename, s.submitted_at, s.analysis_status,
               a.id AS assignment_id, a.title AS assignment_title, a.subject,
               r.combined_similarity_score, r.similarity_label,
               f.review_status, f.review_notes
        FROM student_submissions s
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ?
    """
    params = [user["id"]]

    if q:
        query += " AND (s.title LIKE ? OR s.source_filename LIKE ? OR a.title LIKE ? OR a.subject LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])

    if filter_asgn:
        query += " AND s.assignment_id = ?"
        params.append(filter_asgn)

    if filter_lang:
        query += " AND LOWER(s.programming_language) = ?"
        params.append(filter_lang.lower())

    if filter_status:
        if filter_status == "reviewed":
            query += " AND f.review_status IN ('Reviewed', 'No Concern Identified')"
        elif filter_status == "completed":
            query += " AND s.analysis_status = 'completed'"
        elif filter_status == "pending":
            query += " AND (s.analysis_status = 'pending' OR f.review_status = 'Pending Review' OR f.review_status IS NULL)"

    if filter_band:
        query += " AND r.similarity_label = ?"
        params.append(filter_band)

    query += " ORDER BY s.submitted_at DESC"

    all_subs = conn.execute(query, params).fetchall()
    assignments = conn.execute("SELECT id, title FROM assignments ORDER BY title").fetchall()
    conn.close()

    return render_template(
        "student/submissions.html",
        user=user,
        submissions=all_subs,
        assignments=assignments,
        total_count=total_count,
        completed_count=completed_count,
        pending_count=pending_count,
        reviewed_count=reviewed_count,
        q=q,
        filter_asgn=filter_asgn,
        filter_lang=filter_lang,
        filter_status=filter_status,
        filter_band=filter_band,
        languages=config.LANGUAGE_DISPLAY_NAMES
    )

@student_bp.route("/submission/<int:sub_id>")
@login_required
@role_required("student")
def submission_detail(sub_id):
    user = get_current_user()
    conn = database.get_db_connection()

    sub = conn.execute("""
        SELECT s.id, s.student_id, s.title, s.programming_language, s.source_filename,
               s.source_code, s.analysis_status, s.submitted_at,
               a.title AS assignment_title, a.subject, a.description AS assignment_desc,
               r.id AS result_id, r.text_similarity_score, r.ast_similarity_score, r.combined_similarity_score,
               r.similarity_label, r.analysis_summary, r.analyzed_at,
               f.review_status, f.review_notes, f.reviewed_at
        FROM student_submissions s
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.id = ?
    """, (sub_id,)).fetchone()

    if not sub:
        conn.close()
        flash("Submission not found.", "warning")
        return redirect(url_for("student.submissions"))

    # Strict access control: Student can only view their own submission
    if sub["student_id"] != user["id"]:
        conn.close()
        flash("Access denied: You cannot view submissions belonging to other students.", "danger")
        return abort(403)

    # Matched evidence line numbers for student code
    student_matched_lines = set()
    matching_spans = []
    if sub["result_id"]:
        ev_rows = conn.execute("""
            SELECT student_code_lines, details FROM matched_evidence WHERE analysis_result_id = ?
        """, (sub["result_id"],)).fetchall()
        for ev in ev_rows:
            if ev["student_code_lines"]:
                try:
                    ranges = json.loads(ev["student_code_lines"])
                    for r_start, r_end in ranges:
                        student_matched_lines.update(range(r_start, r_end + 1))
                except Exception:
                    pass
            if ev["details"]:
                try:
                    matching_spans = json.loads(ev["details"])
                except Exception:
                    pass

    # Check for existing student clarification request
    clarification = conn.execute("""
        SELECT * FROM clarification_requests 
        WHERE submission_id = ? AND student_id = ? 
        ORDER BY created_at DESC LIMIT 1
    """, (sub_id, user["id"])).fetchone()

    conn.close()

    return render_template(
        "student/submission_detail.html",
        user=user,
        sub=sub,
        student_matched_lines=student_matched_lines,
        matching_spans=matching_spans,
        clarification=clarification
    )

@student_bp.route("/submission/<int:sub_id>/clarification", methods=["POST"])
@login_required
@role_required("student")
def submit_clarification(sub_id):
    user = get_current_user()
    conn = database.get_db_connection()

    sub = conn.execute("SELECT id, student_id FROM student_submissions WHERE id = ?", (sub_id,)).fetchone()
    if not sub or sub["student_id"] != user["id"]:
        conn.close()
        flash("Unauthorized action.", "danger")
        return abort(403)

    statement = request.form.get("statement", "").strip()
    if not statement:
        flash("Clarification statement cannot be empty.", "warning")
        conn.close()
        return redirect(url_for("student.submission_detail", sub_id=sub_id))

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clarification_requests (submission_id, student_id, student_statement, status)
        VALUES (?, ?, ?, 'Submitted')
    """, (sub_id, user["id"], statement))
    conn.commit()
    conn.close()

    flash("Your clarification request has been submitted for faculty review.", "success")
    return redirect(url_for("student.submission_detail", sub_id=sub_id))
