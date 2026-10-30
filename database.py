import sqlite3
import csv
import os
from werkzeug.security import generate_password_hash
from datetime import datetime
import config

def get_db_connection():
    """Returns a SQLite connection with row factory configured to sqlite3.Row."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes the database schema and seeds initial demo data if needed."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.UPLOADS_SUBMISSIONS_DIR, exist_ok=True)
    os.makedirs(config.UPLOADS_HISTORICAL_DIR, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'faculty')),
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Assignments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT,
            allowed_languages TEXT NOT NULL,
            deadline TEXT,
            created_by INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # 3. Historical Submissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT DEFAULT 'DEMO-HIST-001',
            academic_year TEXT NOT NULL,
            subject TEXT NOT NULL,
            assignment_name TEXT NOT NULL,
            programming_language TEXT NOT NULL,
            source_filename TEXT NOT NULL,
            source_code TEXT NOT NULL,
            batch_label TEXT,
            is_authorized_for_students INTEGER DEFAULT 1,
            uploaded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    """)

    # Column migrations if table previously existed
    cursor.execute("PRAGMA table_info(historical_submissions)")
    existing_hist_cols = [col[1] for col in cursor.fetchall()]
    if "student_id" not in existing_hist_cols:
        cursor.execute("ALTER TABLE historical_submissions ADD COLUMN student_id TEXT DEFAULT 'STU001'")
    if "is_authorized_for_students" not in existing_hist_cols:
        cursor.execute("ALTER TABLE historical_submissions ADD COLUMN is_authorized_for_students INTEGER DEFAULT 1")

    # 4. Student Submissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            title TEXT,
            programming_language TEXT NOT NULL,
            source_filename TEXT,
            source_code TEXT NOT NULL,
            analysis_status TEXT DEFAULT 'completed',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (assignment_id) REFERENCES assignments(id)
        )
    """)

    # 5. Analysis Results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER UNIQUE NOT NULL,
            matched_historical_id INTEGER,
            text_similarity_score REAL DEFAULT 0.0,
            ast_similarity_score REAL DEFAULT 0.0,
            combined_similarity_score REAL DEFAULT 0.0,
            similarity_label TEXT DEFAULT 'Low Similarity',
            analysis_summary TEXT,
            grok_explanation TEXT,
            grok_explained_at TIMESTAMP,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES student_submissions(id) ON DELETE CASCADE,
            FOREIGN KEY (matched_historical_id) REFERENCES historical_submissions(id) ON DELETE SET NULL
        )
    """)

    # Column migrations for analysis_results
    cursor.execute("PRAGMA table_info(analysis_results)")
    existing_res_cols = [col[1] for col in cursor.fetchall()]
    if "grok_explanation" not in existing_res_cols:
        cursor.execute("ALTER TABLE analysis_results ADD COLUMN grok_explanation TEXT")
    if "grok_explained_at" not in existing_res_cols:
        cursor.execute("ALTER TABLE analysis_results ADD COLUMN grok_explained_at TIMESTAMP")


    # 6. Matched Evidence table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matched_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_result_id INTEGER NOT NULL,
            student_code_lines TEXT,
            historical_code_lines TEXT,
            evidence_type TEXT,
            details TEXT,
            FOREIGN KEY (analysis_result_id) REFERENCES analysis_results(id) ON DELETE CASCADE
        )
    """)

    # 7. Faculty Reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faculty_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_result_id INTEGER UNIQUE NOT NULL,
            faculty_id INTEGER NOT NULL,
            review_status TEXT DEFAULT 'Pending Review',
            review_notes TEXT,
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_result_id) REFERENCES analysis_results(id) ON DELETE CASCADE,
            FOREIGN KEY (faculty_id) REFERENCES users(id)
        )
    """)

    # 8. Clarification Requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clarification_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            student_statement TEXT NOT NULL,
            status TEXT DEFAULT 'Submitted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES student_submissions(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
    """)

    # 9. Student Notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT DEFAULT 'info',
            link_url TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

    # Seed demo accounts and initial sample assignments/history
    seed_demo_accounts()
    seed_sample_assignments_and_history()
    seed_sample_notifications()
    seed_sample_student_submissions()

# Re-export seed functions from dedicated seeds module
from seeds import (
    seed_demo_accounts,
    seed_sample_assignments_and_history,
    seed_sample_notifications,
    seed_sample_student_submissions,
)

if __name__ == '__main__':
    init_db()
    print('Database initialized and verified successfully.')
