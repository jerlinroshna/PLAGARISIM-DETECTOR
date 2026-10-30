import re
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

def detect_language_from_code(code_str):
    if not code_str:
        return None
    text = code_str.strip()
    if re.search(r'#include\s*<iostream>|std::|cout\s*<<|cin\s*>>|namespace\s+std|#include\s*<vector>', text, re.IGNORECASE):
        return "cpp"
    if re.search(r'#include\s*<stdio\.h>|#include\s*<stdlib\.h>|#include\s*<string\.h>|printf\s*\(|scanf\s*\(|int\s+main\s*\(', text, re.IGNORECASE):
        return "c"
    if re.search(r'public\s+class\s+|System\.out\.(println|print)|public\s+static\s+void\s+main', text):
        return "java"
    if re.search(r'def\s+[a-zA-Z0-9_]+\s*\(|import\s+[a-zA-Z0-9_]+|from\s+[a-zA-Z0-9_]+\s+import|if\s+__name__\s*==|elif\s+|print\s*\(', text):
        return "python"
    if re.search(r'console\.log\s*\(|function\s+[a-zA-Z0-9_]+\s*\(|const\s+[a-zA-Z0-9_]+\s*=|let\s+[a-zA-Z0-9_]+\s*=', text):
        return "javascript"
    return None

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

        submission_mode = request.form.get("submission_mode", "auto").strip()
        source_code = ""
        source_filename = "submission_code"

        is_paste = (submission_mode == "paste") or (bool(code_input) and (not uploaded_file or uploaded_file.filename == ""))

        if is_paste:
            if not code_input:
                flash("Submission cannot be empty. Please paste your source code into the editor.", "danger")
                conn.close()
                return redirect(url_for("student.submit"))

            source_code = code_input

            # Intelligent language auto-detection for pasted code
            if not language or language == "auto":
                detected = detect_language_from_code(code_input)
                if detected:
                    language = detected
                elif allowed_langs and len(allowed_langs) == 1:
                    language = allowed_langs[0]
                elif allowed_langs:
                    language = allowed_langs[0]
                else:
                    language = "python"

            ext_map = {"python": "py", "c": "c", "cpp": "cpp", "java": "java", "javascript": "js"}
            ext = ext_map.get(language, "txt")
            source_filename = f"pasted_code.{ext}"
        else:
            if not uploaded_file or uploaded_file.filename == "":
                # Fallback to code_input if provided
                if code_input:
                    source_code = code_input
                    if not language or language == "auto":
                        detected = detect_language_from_code(code_input)
                        language = detected or (allowed_langs[0] if allowed_langs else "python")
                    ext_map = {"python": "py", "c": "c", "cpp": "cpp", "java": "java", "javascript": "js"}
                    source_filename = f"pasted_code.{ext_map.get(language, 'txt')}"
                else:
                    flash("Please upload a source code file or paste code into the editor.", "danger")
                    conn.close()
                    return redirect(url_for("student.submit"))
            else:
                raw_filename = secure_filename(uploaded_file.filename)
                ext = raw_filename.rsplit(".", 1)[-1].lower() if "." in raw_filename else ""

                if ext not in config.ALLOWED_EXTENSIONS:
                    flash(
                        f"Unsupported file extension '.{ext}'. Supported extensions: {', '.join(config.ALLOWED_EXTENSIONS.keys())}.",
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
        "SELECT id, title, subject, description, allowed_languages, deadline FROM assignments WHERE is_active = 1 ORDER BY id ASC"
    ).fetchall()
    conn.close()

    return render_template(
        "student/submit.html",
        user=user,
        assignments=assignments,
        languages=config.LANGUAGE_DISPLAY_NAMES,
        supported_languages=SUPPORTED_ANALYSIS_LANGUAGES
    )
