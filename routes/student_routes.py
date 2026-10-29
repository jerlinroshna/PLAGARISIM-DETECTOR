import os
import csv
import io
import json
from datetime import datetime, timedelta
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

    # 1. Summary Cards (strictly scoped to authenticated session user['id'])
    total_sub = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ?",
        (user["id"],)
    ).fetchone()[0]

    reports_ready = conn.execute("""
        SELECT COUNT(*) FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        WHERE s.student_id = ? AND s.analysis_status = 'completed'
    """, (user["id"],)).fetchone()[0]

    active_sub = conn.execute("""
        SELECT COUNT(*) FROM student_submissions
        WHERE student_id = ? AND analysis_status IN ('pending', 'processing')
    """, (user["id"],)).fetchone()[0]

    # 2. Chart C: My Submission Status (Completed, Processing, Failed)
    status_rows = conn.execute("""
        SELECT analysis_status, COUNT(*) AS count
        FROM student_submissions
        WHERE student_id = ?
        GROUP BY analysis_status
    """, (user["id"],)).fetchall()

    completed_count = 0
    processing_count = 0
    failed_count = 0
    for row in status_rows:
        st = (row["analysis_status"] or "").lower().strip()
        cnt = row["count"]
        if st in ("completed", "screened", "success"):
            completed_count += cnt
        elif st in ("pending", "processing", "queued", "analyzing"):
            processing_count += cnt
        elif st in ("failed", "error"):
            failed_count += cnt
        else:
            processing_count += cnt

    status_total = completed_count + processing_count + failed_count
    status_chart = {
        "completed": completed_count,
        "processing": processing_count,
        "failed": failed_count,
        "total": status_total,
        "completed_pct": round((completed_count / status_total * 100), 1) if status_total > 0 else 0,
        "processing_pct": round((processing_count / status_total * 100), 1) if status_total > 0 else 0,
        "failed_pct": round((failed_count / status_total * 100), 1) if status_total > 0 else 0,
    }

    # 3. Chart D: My Similarity Distribution (0-20%, 21-40%, 41-60%, 61-80%, 81-100%)
    sim_scores = conn.execute("""
        SELECT r.combined_similarity_score
        FROM student_submissions s
        JOIN analysis_results r ON s.id = r.submission_id
        WHERE s.student_id = ? AND s.analysis_status = 'completed' AND r.combined_similarity_score IS NOT NULL
    """, (user["id"],)).fetchall()

    sim_buckets = {
        "b0_20": 0,
        "b21_40": 0,
        "b41_60": 0,
        "b61_80": 0,
        "b81_100": 0
    }
    total_scored_reports = len(sim_scores)
    for row in sim_scores:
        score = float(row["combined_similarity_score"])
        if score <= 20.0:
            sim_buckets["b0_20"] += 1
        elif score <= 40.0:
            sim_buckets["b21_40"] += 1
        elif score <= 60.0:
            sim_buckets["b41_60"] += 1
        elif score <= 80.0:
            sim_buckets["b61_80"] += 1
        else:
            sim_buckets["b81_100"] += 1

    max_sim_bucket = max(sim_buckets.values()) if total_scored_reports > 0 else 0
    sim_chart = {
        "total_reports": total_scored_reports,
        "max_count": max_sim_bucket,
        "b0_20": {"count": sim_buckets["b0_20"], "pct": round(sim_buckets["b0_20"] / total_scored_reports * 100, 1) if total_scored_reports > 0 else 0},
        "b21_40": {"count": sim_buckets["b21_40"], "pct": round(sim_buckets["b21_40"] / total_scored_reports * 100, 1) if total_scored_reports > 0 else 0},
        "b41_60": {"count": sim_buckets["b41_60"], "pct": round(sim_buckets["b41_60"] / total_scored_reports * 100, 1) if total_scored_reports > 0 else 0},
        "b61_80": {"count": sim_buckets["b61_80"], "pct": round(sim_buckets["b61_80"] / total_scored_reports * 100, 1) if total_scored_reports > 0 else 0},
        "b81_100": {"count": sim_buckets["b81_100"], "pct": round(sim_buckets["b81_100"] / total_scored_reports * 100, 1) if total_scored_reports > 0 else 0},
    }

    # 4. Chart E: My Programming Languages (reliable stored metadata)
    lang_rows = conn.execute("""
        SELECT programming_language, COUNT(*) AS count
        FROM student_submissions
        WHERE student_id = ?
        GROUP BY programming_language
        ORDER BY count DESC
    """, (user["id"],)).fetchall()

    lang_display_map = getattr(config, "LANGUAGE_DISPLAY_NAMES", {
        "python": "Python", "java": "Java", "c": "C", "cpp": "C++", "javascript": "JavaScript"
    })
    total_langs_count = sum(r["count"] for r in lang_rows)
    languages_data = []
    for r in lang_rows:
        raw_l = (r["programming_language"] or "").strip().lower()
        display_name = lang_display_map.get(raw_l, raw_l.upper() if len(raw_l) <= 4 else raw_l.capitalize())
        cnt = r["count"]
        pct = round((cnt / total_langs_count * 100), 1) if total_langs_count > 0 else 0
        languages_data.append({
            "key": raw_l,
            "name": display_name,
            "count": cnt,
            "pct": pct
        })

    # 5. Chart F: My Monthly Submission Activity (recent 6 months)
    now = datetime.now()
    monthly_activity = []
    for i in range(5, -1, -1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        ym_str = f"{year:04d}-{month:02d}"
        dt = datetime(year, month, 1)
        cnt = conn.execute(
            "SELECT COUNT(*) FROM student_submissions WHERE student_id = ? AND SUBSTR(submitted_at, 1, 7) = ?",
            (user["id"], ym_str)
        ).fetchone()[0]
        monthly_activity.append({
            "ym": ym_str,
            "label": dt.strftime("%b %Y"),
            "short_label": dt.strftime("%b"),
            "count": cnt
        })

    max_monthly = max((m["count"] for m in monthly_activity), default=0)
    has_monthly_data = any(m["count"] > 0 for m in monthly_activity)
    for m in monthly_activity:
        m["bar_height"] = round((m["count"] / max_monthly * 85), 1) if max_monthly > 0 else 0

    conn.close()

    return render_template(
        "student/dashboard.html",
        user=user,
        total_sub=total_sub,
        reports_ready=reports_ready,
        active_sub=active_sub,
        status_chart=status_chart,
        sim_chart=sim_chart,
        languages_data=languages_data,
        total_langs_count=total_langs_count,
        monthly_activity=monthly_activity,
        max_monthly=max_monthly,
        has_monthly_data=has_monthly_data
    )

@student_bp.route("/active-submissions")
@login_required
@role_required("student")
def active_submissions():
    user = get_current_user()
    conn = database.get_db_connection()
    submissions = conn.execute("""
        SELECT s.id, s.title, s.programming_language, s.source_filename, s.submitted_at, s.analysis_status,
               a.title AS assignment_title, a.subject
        FROM student_submissions s
        JOIN assignments a ON s.assignment_id = a.id
        WHERE s.student_id = ? AND s.analysis_status IN ('pending', 'processing')
        ORDER BY s.submitted_at DESC
    """, (user["id"],)).fetchall()
    conn.close()
    return render_template("student/active_submissions.html", user=user, submissions=submissions)

@student_bp.route("/recent-submissions")
@login_required
@role_required("student")
def recent_submissions():
    user = get_current_user()
    conn = database.get_db_connection()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    per_page = 15
    offset = (page - 1) * per_page

    total_count = conn.execute(
        "SELECT COUNT(*) FROM student_submissions WHERE student_id = ?",
        (user["id"],)
    ).fetchone()[0]

    submissions = conn.execute("""
        SELECT s.id, s.title, s.programming_language, s.source_filename, s.submitted_at, s.analysis_status,
               a.title AS assignment_title, a.subject,
               r.id AS result_id, r.combined_similarity_score, r.similarity_label,
               f.review_status
        FROM student_submissions s
        JOIN assignments a ON s.assignment_id = a.id
        LEFT JOIN analysis_results r ON s.id = r.submission_id
        LEFT JOIN faculty_reviews f ON r.id = f.analysis_result_id
        WHERE s.student_id = ?
        ORDER BY s.submitted_at DESC
        LIMIT ? OFFSET ?
    """, (user["id"], per_page, offset)).fetchall()
    conn.close()

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    return render_template(
        "student/recent_submissions.html",
        user=user,
        submissions=submissions,
        page=page,
        total_pages=total_pages,
        total_count=total_count
    )

@student_bp.route("/assignments")
@login_required
@role_required("student")
def assignments():
    user = get_current_user()
    conn = database.get_db_connection()

    all_assignments = conn.execute("""
        SELECT a.id, a.title, a.subject, a.description, a.allowed_languages, a.deadline, a.is_active,
               sub.id AS submission_id, sub.analysis_status, res.combined_similarity_score, res.similarity_label
        FROM assignments a
        LEFT JOIN (
            SELECT s1.id, s1.assignment_id, s1.analysis_status
            FROM student_submissions s1
            WHERE s1.student_id = ?
            AND s1.id = (
                SELECT MAX(s2.id) FROM student_submissions s2
                WHERE s2.assignment_id = s1.assignment_id AND s2.student_id = ?
            )
        ) sub ON a.id = sub.assignment_id
        LEFT JOIN analysis_results res ON sub.id = res.submission_id
        WHERE a.is_active = 1
        ORDER BY a.created_at DESC
    """, (user["id"], user["id"])).fetchall()
    conn.close()

    return render_template("student/assignments.html", user=user, assignments=all_assignments)

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
