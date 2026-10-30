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
from routes.student import student_bp, SUPPORTED_ANALYSIS_LANGUAGES

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
