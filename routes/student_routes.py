import os
import csv
import io
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from auth import login_required, role_required, get_current_user
import config
import database
from analyzers.comparator import CodeComparator

student_bp = Blueprint("student", __name__, url_prefix="/student")

SUPPORTED_ANALYSIS_LANGUAGES = {"python", "java", "c", "cpp", "javascript"}

@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    user = get_current_user()
    conn = database.get_db_connection()

    # Submission metrics for this student
    total_sub = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ?",
        (user["id"],)
    ).fetchone()[0]

    completed_sub = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ? AND analysis_status = 'completed'",
        (user["id"],)
    ).fetchone()[0]

    pending_sub = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ? AND analysis_status = 'pending'",
        (user["id"],)
    ).fetchone()[0]

    # Authorized historical submissions available
    historical_count = conn.execute(
        "SELECT COUNT(*) FROM historical_submissions WHERE is_authorized_for_students = 1"
    ).fetchone()[0]

    # Active assignments count and list
    active_assignments_count = conn.execute(
        "SELECT COUNT(*) FROM assignments WHERE is_active = 1"
    ).fetchone()[0]

    upcoming_assignments = conn.execute("""
        SELECT id, title, subject, description, allowed_languages, deadline, is_active
        FROM assignments
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 4
    """).fetchall()

    # Reviewed count for this student
    reviewed_sub = conn.execute("""
        SELECT COUNT(*) FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ? AND f.review_status IN ('Reviewed', 'No Concern Identified')
    """, (user["id"],)).fetchone()[0]

    # Similarity breakdown for donut/distribution chart
    low_sim_count = conn.execute("""
        SELECT COUNT(*) FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        WHERE s.student_id = ? AND r.similarity_label = 'Low Similarity'
    """, (user["id"],)).fetchone()[0]

    med_sim_count = conn.execute("""
        SELECT COUNT(*) FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        WHERE s.student_id = ? AND r.similarity_label = 'Medium Similarity'
    """, (user["id"],)).fetchone()[0]

    high_sim_count = conn.execute("""
        SELECT COUNT(*) FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        WHERE s.student_id = ? AND r.similarity_label = 'High Similarity'
    """, (user["id"],)).fetchone()[0]

    # Recent submissions (last 5) with review status
    recent_submissions = conn.execute("""
        SELECT s.id, s.title, s.programming_language, s.source_filename, s.submitted_at, s.analysis_status,
               a.title AS assignment_title, a.subject,
               r.combined_similarity_score, r.similarity_label,
               f.review_status
        FROM student_submissions s
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ?
        ORDER BY s.submitted_at DESC
        LIMIT 5
    """, (user["id"],)).fetchall()

    # Activity calculation: submissions grouped by date
    activity_rows = conn.execute("""
        SELECT SUBSTR(submitted_at, 1, 10) as sub_date, COUNT(*) as cnt
        FROM student_submissions
        WHERE student_id = ?
        GROUP BY sub_date
        ORDER BY sub_date ASC
        LIMIT 7
    """, (user["id"],)).fetchall()
    activity_data = [{"date": row["sub_date"], "count": row["cnt"]} for row in activity_rows]

    conn.close()

    similarity_dist = {
        "low": low_sim_count,
        "medium": med_sim_count,
        "high": high_sim_count,
        "total": low_sim_count + med_sim_count + high_sim_count
    }

    return render_template(
        "student/dashboard.html",
        user=user,
        total_sub=total_sub,
        completed_sub=completed_sub,
        pending_sub=pending_sub,
        reviewed_sub=reviewed_sub,
        historical_count=historical_count,
        active_assignments=active_assignments_count,
        upcoming_assignments=upcoming_assignments,
        recent_submissions=recent_submissions,
        similarity_dist=similarity_dist,
        activity_data=activity_data
    )

@student_bp.route("/submit", methods=["GET", "POST"])
@login_required
@role_required("student")
def submit():
    user = get_current_user()
    conn = database.get_db_connection()

    if request.method == "POST":
        assignment_id = request.form.get("assignment_id")
        title = request.form.get("title", "").strip() or "Untitled Submission"
        language = request.form.get("programming_language", "").lower().strip()
        code_input = request.form.get("code_text", "").strip()
        uploaded_file = request.files.get("code_file")

        # Validation: assignment exists and is active
        asgn = conn.execute(
            "SELECT id, title, allowed_languages, is_active FROM assignments WHERE id = ?",
            (assignment_id,)
        ).fetchone()

        if not asgn or not asgn["is_active"]:
            flash("Selected assignment is not available for submission.", "danger")
            conn.close()
            return redirect(url_for("student.submit"))

        allowed_langs = [l.strip().lower() for l in asgn["allowed_languages"].split(",")]

        source_code = ""
        source_filename = "pasted_code"

        # Check if file was uploaded
        if uploaded_file and uploaded_file.filename != "":
            raw_filename = secure_filename(uploaded_file.filename)
            ext = raw_filename.rsplit(".", 1)[-1].lower() if "." in raw_filename else ""

            if ext not in config.ALLOWED_EXTENSIONS:
                flash(
                    f"Unsupported file extension '.{ext}'. Supported extensions: {', '.join(config.ALLOWED_EXTENSIONS.keys())}. Unsupported languages (PHP, Ruby, Rust, Go, C#, Swift) cannot be analyzed.",
                    "danger"
                )
                conn.close()
                return redirect(url_for("student.submit"))

            detected_lang = config.ALLOWED_EXTENSIONS[ext]
            if not language or language == "auto":
                language = detected_lang

            source_filename = raw_filename
            try:
                source_code = uploaded_file.read().decode("utf-8", errors="replace")
            except Exception as e:
                flash(f"Error reading uploaded file: {str(e)}", "danger")
                conn.close()
                return redirect(url_for("student.submit"))
        else:
            # Code was pasted in textarea
            if not code_input:
                flash("Submission cannot be empty. Please upload a source code file or paste code into the editor.", "danger")
                conn.close()
                return redirect(url_for("student.submit"))
            source_code = code_input
            if not language or language == "auto":
                flash("Please select a programming language for pasted code.", "danger")
                conn.close()
                return redirect(url_for("student.submit"))
            source_filename = f"submission.{language}"

        if not source_code.strip():
            flash("Submission cannot be empty. Please provide valid source code.", "danger")
            conn.close()
            return redirect(url_for("student.submit"))

        # Explicit check for supported analyzer language
        if language not in SUPPORTED_ANALYSIS_LANGUAGES:
            flash(
                f"Language '{language}' is not supported by the AST analyzer. Fully supported languages: Python (.py), C (.c), C++ (.cpp), Java (.java), JavaScript (.js).",
                "danger"
            )
            conn.close()
            return redirect(url_for("student.submit"))

        if language not in allowed_langs:
            flash(
                f"Language '{language}' is not permitted for this assignment. Allowed languages for this assignment: {', '.join(allowed_langs)}.",
                "danger"
            )
            conn.close()
            return redirect(url_for("student.submit"))

        # Save submission to database
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO student_submissions 
            (student_id, assignment_id, title, programming_language, source_filename, source_code, analysis_status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (user["id"], assignment_id, title, language, source_filename, source_code))
        submission_id = cursor.lastrowid
        conn.commit()

        # Save file to disk
        try:
            save_path = os.path.join(config.UPLOADS_SUBMISSIONS_DIR, f"sub_{submission_id}_{source_filename}")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(source_code)
        except Exception:
            pass  # primary source is persisted in SQLite

        # Run automated plagiarism analysis against historical submissions
        try:
            CodeComparator.analyze_submission(submission_id)
        except Exception as e:
            print(f"Error analyzing submission {submission_id}: {e}")

        # Add notification for the student
        try:
            cursor.execute("""
                INSERT INTO student_notifications (student_id, title, message, category, link_url, is_read)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                user["id"],
                f"Screening Complete: {title}",
                f"Your submission #{submission_id} for '{asgn['title']}' has completed automated AST and token screening.",
                "submission",
                url_for("student.submission_detail", sub_id=submission_id)
            ))
            conn.commit()
        except Exception:
            pass

        conn.close()

        flash("Code submitted successfully! Automated academic integrity screening completed.", "success")
        return redirect(url_for("student.submission_detail", sub_id=submission_id))

    # GET request: load active assignments
    assignments = conn.execute(
        "SELECT id, title, subject, description, allowed_languages, deadline FROM assignments WHERE is_active = 1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return render_template(
        "student/submit.html",
        user=user,
        assignments=assignments,
        languages=config.LANGUAGE_DISPLAY_NAMES,
        supported_languages=SUPPORTED_ANALYSIS_LANGUAGES
    )

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

@student_bp.route("/historical")
@login_required
@role_required("student")
def historical():
    user = get_current_user()
    conn = database.get_db_connection()

    filter_year = request.args.get("year", "").strip()
    filter_lang = request.args.get("language", "").strip()
    search_q = request.args.get("search", "").strip()

    query = """
        SELECT id, academic_year, subject, assignment_name, programming_language,
               source_filename, source_code, batch_label, created_at
        FROM historical_submissions
        WHERE is_authorized_for_students = 1
    """
    params = []

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

    years = conn.execute(
        "SELECT DISTINCT academic_year FROM historical_submissions WHERE is_authorized_for_students = 1 ORDER BY academic_year DESC"
    ).fetchall()

    subjects = conn.execute(
        "SELECT DISTINCT subject FROM historical_submissions WHERE is_authorized_for_students = 1 ORDER BY subject"
    ).fetchall()

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
