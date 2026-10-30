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

@student_bp.route("/reports")
@login_required
@role_required("student")
def reports():
    user = get_current_user()
    conn = database.get_db_connection()

    filter_asgn = request.args.get("assignment", "").strip()
    filter_lang = request.args.get("language", "").strip()
    filter_band = request.args.get("similarity", "").strip()

    # Personal analytics metrics for this student
    total_analyzed = conn.execute("""
        SELECT COUNT(*) FROM analysis_results r
        JOIN student_submissions s ON r.submission_id = s.id
        WHERE s.student_id = ?
    """, (user["id"],)).fetchone()[0]

    high_count = conn.execute("""
        SELECT COUNT(*) FROM analysis_results r
        JOIN student_submissions s ON r.submission_id = s.id
        WHERE s.student_id = ? AND r.similarity_label = 'High Similarity'
    """, (user["id"],)).fetchone()[0]

    medium_count = conn.execute("""
        SELECT COUNT(*) FROM analysis_results r
        JOIN student_submissions s ON r.submission_id = s.id
        WHERE s.student_id = ? AND r.similarity_label = 'Medium Similarity'
    """, (user["id"],)).fetchone()[0]

    low_count = conn.execute("""
        SELECT COUNT(*) FROM analysis_results r
        JOIN student_submissions s ON r.submission_id = s.id
        WHERE s.student_id = ? AND r.similarity_label = 'Low Similarity'
    """, (user["id"],)).fetchone()[0]

    reviewed_count = conn.execute("""
        SELECT COUNT(*) FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ? AND f.review_status IN ('Reviewed', 'No Concern Identified')
    """, (user["id"],)).fetchone()[0]

    stats_row = conn.execute("""
        SELECT AVG(r.combined_similarity_score), MIN(r.combined_similarity_score), MAX(r.combined_similarity_score)
        FROM analysis_results r
        JOIN student_submissions s ON r.submission_id = s.id
        WHERE s.student_id = ?
    """, (user["id"],)).fetchone()

    avg_similarity = round(stats_row[0], 1) if stats_row and stats_row[0] is not None else 0.0
    min_similarity = round(stats_row[1], 1) if stats_row and stats_row[1] is not None else 0.0
    max_similarity = round(stats_row[2], 1) if stats_row and stats_row[2] is not None else 0.0

    # Language usage distribution
    lang_rows = conn.execute("""
        SELECT programming_language, COUNT(*) as cnt
        FROM student_submissions
        WHERE student_id = ?
        GROUP BY programming_language
    """, (user["id"],)).fetchall()
    language_stats = {r["programming_language"].lower(): r["cnt"] for r in lang_rows}

    # Filtered records for this student
    query = """
        SELECT s.id, s.title, s.programming_language, s.submitted_at, s.source_filename,
               a.id AS assignment_id, a.title AS assignment_title, a.subject,
               r.text_similarity_score, r.ast_similarity_score, r.combined_similarity_score,
               r.similarity_label,
               f.review_status, f.review_notes
        FROM student_submissions s
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ? AND r.id IS NOT NULL
    """
    params = [user["id"]]

    if filter_asgn:
        query += " AND s.assignment_id = ?"
        params.append(filter_asgn)

    if filter_lang:
        query += " AND LOWER(s.programming_language) = ?"
        params.append(filter_lang.lower())

    if filter_band:
        query += " AND r.similarity_label = ?"
        params.append(filter_band)

    query += " ORDER BY s.submitted_at DESC"
    records = conn.execute(query, params).fetchall()

    assignments = conn.execute("SELECT id, title FROM assignments ORDER BY title").fetchall()
    conn.close()

    return render_template(
        "student/reports.html",
        user=user,
        records=records,
        assignments=assignments,
        filter_asgn=filter_asgn,
        filter_lang=filter_lang,
        filter_band=filter_band,
        total_analyzed=total_analyzed,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        reviewed_count=reviewed_count,
        avg_similarity=avg_similarity,
        min_similarity=min_similarity,
        max_similarity=max_similarity,
        language_stats=language_stats
    )

@student_bp.route("/reports/export")
@login_required
@role_required("student")
def export_csv_report():
    user = get_current_user()
    conn = database.get_db_connection()

    records = conn.execute("""
        SELECT s.id, s.title, s.programming_language, s.submitted_at, s.source_filename,
               a.title AS assignment_title, a.subject,
               r.text_similarity_score, r.ast_similarity_score, r.combined_similarity_score,
               r.similarity_label,
               f.review_status
        FROM student_submissions s
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ? AND r.id IS NOT NULL
        ORDER BY s.submitted_at DESC
    """, (user["id"],)).fetchall()
    conn.close()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow([
        "Submission ID", "Assignment", "Subject", "Language", "Filename",
        "Submitted At", "Text Similarity %", "AST Similarity %",
        "Combined Similarity %", "Classification", "Faculty Review Status"
    ])
    for r in records:
        writer.writerow([
            r["id"], r["assignment_title"], r["subject"],
            r["programming_language"].upper(), r["source_filename"],
            r["submitted_at"], r["text_similarity_score"] or 0.0,
            r["ast_similarity_score"] or 0.0, r["combined_similarity_score"] or 0.0,
            r["similarity_label"] or "Low Similarity", r["review_status"] or "Pending Review"
        ])

    output = Response(si.getvalue(), mimetype="text/csv")
    output.headers["Content-Disposition"] = f"attachment; filename=plagiarism_report_{user['username']}.csv"
    return output
