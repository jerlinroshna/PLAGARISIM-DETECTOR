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
