import os
import csv
import io
import json
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, 
    abort, Response, send_file, jsonify
)
from auth import login_required, role_required, get_current_user
import config
import database
from analyzers.comparator import CodeComparator
from services.grok_service import GrokService


faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

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

@faculty_bp.route("/assignments", methods=["GET", "POST"])
@login_required
@role_required("faculty")
def assignments():
    user = get_current_user()
    conn = database.get_db_connection()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        deadline = request.form.get("deadline", "").strip()
        langs = request.form.getlist("allowed_languages")

        if not title or not subject:
            flash("Assignment Title and Subject are required.", "danger")
            return redirect(url_for("faculty.assignments"))

        if not langs:
            flash("Please select at least one permitted programming language.", "danger")
            return redirect(url_for("faculty.assignments"))

        allowed_languages_str = ",".join(langs)

        conn.execute("""
            INSERT INTO assignments (title, subject, description, allowed_languages, deadline, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (title, subject, description, allowed_languages_str, deadline, user["id"]))
        conn.commit()
        flash(f"Assignment '{title}' created successfully.", "success")
        conn.close()
        return redirect(url_for("faculty.assignments"))

    all_assignments = conn.execute("""
        SELECT a.id, a.title, a.subject, a.description, a.allowed_languages, 
               a.deadline, a.is_active, a.created_at,
               COUNT(s.id) AS submission_count
        FROM assignments a
        LEFT JOIN student_submissions s ON a.id = s.assignment_id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()

    return render_template(
        "faculty/assignments.html",
        user=user,
        assignments=all_assignments,
        all_languages=config.ALLOWED_EXTENSIONS
    )

@faculty_bp.route("/assignment/<int:asgn_id>/toggle", methods=["POST"])
@login_required
@role_required("faculty")
def toggle_assignment(asgn_id):
    conn = database.get_db_connection()
    asgn = conn.execute("SELECT id, is_active, title FROM assignments WHERE id = ?", (asgn_id,)).fetchone()
    if asgn:
        new_status = 0 if asgn["is_active"] else 1
        conn.execute("UPDATE assignments SET is_active = ? WHERE id = ?", (new_status, asgn_id))
        conn.commit()
        status_label = "enabled" if new_status == 1 else "disabled"
        flash(f"Assignment '{asgn['title']}' has been {status_label}.", "info")
    conn.close()
    return redirect(url_for("faculty.assignments"))

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


@faculty_bp.route("/historical", methods=["GET", "POST"])
@login_required
@role_required("faculty")
def historical_repo():
    user = get_current_user()
    conn = database.get_db_connection()

    if request.method == "POST":
        academic_year = request.form.get("academic_year", "").strip()
        subject = request.form.get("subject", "").strip()
        assignment_name = request.form.get("assignment_name", "").strip()
        student_id_input = request.form.get("student_id", "").strip() or f"HIST-REF-{user['username']}"
        language = request.form.get("programming_language", "").lower().strip()
        batch_label = request.form.get("batch_label", "").strip() or "Standard Historical Submission"
        is_authorized = 1 if request.form.get("is_authorized_for_students") else 0
        code_input = request.form.get("code_text", "").strip()
        uploaded_file = request.files.get("code_file")

        if not academic_year or not subject or not assignment_name:
            flash("Academic Year, Subject, and Assignment Name are required fields.", "danger")
            conn.close()
            return redirect(url_for("faculty.historical_repo"))

        source_code = ""
        source_filename = "historical_code"

        if uploaded_file and uploaded_file.filename != "":
            raw_filename = secure_filename(uploaded_file.filename)
            ext = raw_filename.rsplit(".", 1)[-1].lower() if "." in raw_filename else ""

            if ext not in config.ALLOWED_EXTENSIONS:
                flash(f"Unsupported file type .{ext}.", "danger")
                conn.close()
                return redirect(url_for("faculty.historical_repo"))

            detected_lang = config.ALLOWED_EXTENSIONS[ext]
            if not language or language == "auto":
                language = detected_lang

            source_filename = raw_filename
            try:
                source_code = uploaded_file.read().decode("utf-8", errors="replace")
            except Exception as e:
                flash(f"Error reading file: {str(e)}", "danger")
                conn.close()
                return redirect(url_for("faculty.historical_repo"))
        else:
            if not code_input:
                flash("Please upload a source code file or paste code in the editor.", "danger")
                conn.close()
                return redirect(url_for("faculty.historical_repo"))
            source_code = code_input
            if not language or language == "auto":
                flash("Please select a programming language for pasted code.", "danger")
                conn.close()
                return redirect(url_for("faculty.historical_repo"))
            source_filename = f"historical_{assignment_name.replace(' ', '_')}.{language}"

                # Prevent duplicate identical submission for same student, assignment, year, and filename
        existing_dup = conn.execute("""
            SELECT id FROM historical_submissions 
            WHERE student_id = ? AND assignment_name = ? AND academic_year = ? AND source_filename = ?
        """, (student_id_input, assignment_name, academic_year, source_filename)).fetchone()
        if existing_dup:
            flash(f"A historical submission for Student '{student_id_input}' and assignment '{assignment_name}' already exists (ID #{existing_dup['id']}). Duplicate entry skipped.", "warning")
            conn.close()
            return redirect(url_for("faculty.historical_repo"))

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historical_submissions 
            (student_id, academic_year, subject, assignment_name, programming_language, source_filename, source_code, batch_label, is_authorized_for_students, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id_input, academic_year, subject, assignment_name, language, source_filename, source_code, batch_label, is_authorized, user["id"]))
        hist_id = cursor.lastrowid
        conn.commit()

        # Save to uploads/historical
        try:
            save_path = os.path.join(config.UPLOADS_HISTORICAL_DIR, f"hist_{hist_id}_{source_filename}")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(source_code)
        except Exception:
            pass

        conn.close()
        flash(f"Historical code record '{source_filename}' (Student Ref: {student_id_input}, AY {academic_year}) uploaded successfully.", "success")
        return redirect(url_for("faculty.historical_repo"))

    # GET filters
    filter_year = request.args.get("year", "").strip()
    filter_subject = request.args.get("subject", "").strip()
    filter_lang = request.args.get("language", "").strip()
    filter_auth = request.args.get("authorized", "").strip()
    search_q = request.args.get("search", "").strip()

    query = """
        SELECT h.id, h.student_id, h.academic_year, h.subject, h.assignment_name, h.programming_language,
               h.source_filename, h.batch_label, h.is_authorized_for_students, h.created_at, h.source_code,
               u.username AS uploaded_by_username
        FROM historical_submissions h
        LEFT JOIN users u ON h.uploaded_by = u.id
        WHERE 1=1
    """
    params = []

    if filter_year:
        query += " AND h.academic_year = ?"
        params.append(filter_year)

    if filter_subject:
        query += " AND h.subject LIKE ?"
        params.append(f"%{filter_subject}%")

    if filter_lang:
        query += " AND LOWER(h.programming_language) = ?"
        params.append(filter_lang.lower())

    if filter_auth == "1":
        query += " AND h.is_authorized_for_students = 1"
    elif filter_auth == "0":
        query += " AND h.is_authorized_for_students = 0"

    if search_q:
        query += " AND (h.assignment_name LIKE ? OR h.subject LIKE ? OR h.student_id LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"])

    query += " ORDER BY h.academic_year DESC, h.created_at DESC"

    records = conn.execute(query, params).fetchall()

    years = conn.execute("SELECT DISTINCT academic_year FROM historical_submissions ORDER BY academic_year DESC").fetchall()
    subjects = conn.execute("SELECT DISTINCT subject FROM historical_submissions ORDER BY subject").fetchall()
    conn.close()

    return render_template(
        "faculty/historical_repo.html",
        user=user,
        records=records,
        years=years,
        subjects=subjects,
        filter_year=filter_year,
        filter_subject=filter_subject,
        filter_lang=filter_lang,
        filter_auth=filter_auth,
        search_q=search_q,
        languages=config.LANGUAGE_DISPLAY_NAMES
    )

@faculty_bp.route("/historical/<int:hist_id>/delete", methods=["POST"])
@login_required
@role_required("faculty")
def delete_historical(hist_id):
    conn = database.get_db_connection()
    conn.execute("DELETE FROM historical_submissions WHERE id = ?", (hist_id,))
    conn.commit()
    conn.close()
    flash("Historical record successfully removed from the repository.", "info")
    return redirect(url_for("faculty.historical_repo"))

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

@faculty_bp.route("/analysis/<int:sub_id>/explain", methods=["POST"])
@login_required
@role_required("faculty")
def explain_analysis(sub_id):
    """Faculty-only endpoint to explain plagiarism comparison results using xAI Grok."""
    force_refresh = False
    if request.is_json:
        force_refresh = bool(request.json.get("refresh", False))
    elif request.form:
        force_refresh = bool(request.form.get("refresh", False))

    result = GrokService.explain_submission(sub_id, force_refresh=force_refresh)
    if not result.get("success"):
        err_lower = result.get("error", "").lower()
        status_code = 400 if ("missing" in err_lower or "not found" in err_lower) else 502
        return jsonify(result), status_code

    return jsonify(result), 200

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
