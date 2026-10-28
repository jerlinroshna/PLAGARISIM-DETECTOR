"""
Idempotent test data seed script for STU001.
Sets up:
- ~12 submissions across assignments with mixed similarity bands:
  - 1 High flagged submission (without clarification)
  - 1 Pending submission
  - Several Low similarity submissions
  - A few Medium similarity submissions
  - Spread across the last 6 weeks
- 5 student notifications (3 unread, 2 read)
- 4 academic assignments with diverse deadlines:
  - One under 24h (urgent countdown)
  - One medium (5 days)
  - One longer term (14 days)
  - One closed / deadline passed
- Leaves other accounts (e.g. STU050) untouched so fresh empty states can be verified.
"""

from datetime import datetime, timedelta
import database

def seed_test_data():
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch STU001 user
    stu = cursor.execute("SELECT id, username FROM users WHERE username = 'STU001'").fetchone()
    if not stu:
        print("STU001 not found! Initializing database first...")
        database.init_db()
        stu = cursor.execute("SELECT id, username FROM users WHERE username = 'STU001'").fetchone()

    stu_id = stu["id"]
    print(f"Seeding demo data for STU001 (ID: {stu_id})...")

    # 2. Configure 4 Assignments
    now = datetime.now()
    deadline_under_24h = (now + timedelta(hours=18, minutes=45)).strftime("%Y-%m-%d %H:%M:00")
    deadline_medium = (now + timedelta(days=5, hours=6)).strftime("%Y-%m-%d %H:%M:00")
    deadline_long = (now + timedelta(days=14, hours=12)).strftime("%Y-%m-%d %H:%M:00")
    deadline_closed = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:00")

    assignments_config = [
        (1, "CS201: Digit Manipulation & Loop Algorithms", "CS201", "Core algorithmic implementations of iterative loops, prime sieves, and recursive number reductions.", "python,c,cpp,java", deadline_under_24h, 1),
        (2, "CS301: Fibonacci & Sequence Generation", "CS301", "Dynamic programming vs matrix exponentiation for sequence generators with complexity constraints.", "python,java,javascript", deadline_medium, 1),
        (3, "CS302: Bank Account Transaction Manager", "CS302", "Object-oriented model for ledger records, transaction atomicity, and balance auditing.", "java,cpp,python", deadline_long, 1),
        (4, "CS401: String Tokenizer & Palindrome Checker", "CS401", "Lexical parsing, sliding window substring matching, and normalized token verification.", "c,cpp,javascript", deadline_closed, 0)
    ]

    for asgn_id, title, subj, desc, langs, dline, is_act in assignments_config:
        existing = cursor.execute("SELECT id FROM assignments WHERE id = ?", (asgn_id,)).fetchone()
        if existing:
            cursor.execute("""
                UPDATE assignments
                SET title = ?, subject = ?, description = ?, allowed_languages = ?, deadline = ?, is_active = ?
                WHERE id = ?
            """, (title, subj, desc, langs, dline, is_act, asgn_id))
        else:
            cursor.execute("""
                INSERT INTO assignments (id, title, subject, description, allowed_languages, deadline, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (asgn_id, title, subj, desc, langs, dline, is_act))

    # 3. Clean existing submissions & notifications for STU001 to ensure exact test counts
    sub_ids = [r[0] for r in cursor.execute("SELECT id FROM student_submissions WHERE student_id = ?", (stu_id,)).fetchall()]
    for sid in sub_ids:
        cursor.execute("DELETE FROM faculty_reviews WHERE analysis_result_id IN (SELECT id FROM analysis_results WHERE submission_id = ?)", (sid,))
        cursor.execute("DELETE FROM matched_evidence WHERE analysis_result_id IN (SELECT id FROM analysis_results WHERE submission_id = ?)", (sid,))
        cursor.execute("DELETE FROM analysis_results WHERE submission_id = ?", (sid,))
        cursor.execute("DELETE FROM clarification_requests WHERE submission_id = ?", (sid,))
    cursor.execute("DELETE FROM student_submissions WHERE student_id = ?", (stu_id,))
    cursor.execute("DELETE FROM student_notifications WHERE student_id = ?", (stu_id,))

    # 4. Seed ~12 Submissions across 6 weeks
    # Structure: (asgn_id, title, lang, filename, days_ago, status, text_sim, ast_sim, comb_sim, label, review_status)
    submissions_data = [
        # Today / Yesterday
        (1, "Digit Counter Solution v2", "python", "solution.py", 0, "completed", 12.0, 14.5, 13.5, "Low Similarity", "Cleared"),
        (2, "Matrix Sequence Generator", "python", "fibonacci.py", 1, "pending", 0.0, 0.0, 0.0, "Low Similarity", "Pending Review"),
        # Last 7 days
        (1, "Recursive Digit Sum", "cpp", "digits.cpp", 3, "completed", 18.0, 20.0, 19.2, "Low Similarity", "Cleared"),
        (2, "Dynamic Fib Generator", "java", "FibSeq.java", 5, "completed", 72.0, 82.5, 78.3, "High Similarity", "Under Investigation"), # Flagged, no clarification
        (3, "Account Transaction Ledger", "java", "AccountManager.java", 6, "completed", 32.0, 42.0, 38.0, "Medium Similarity", "Reviewed"),
        # Week 2 (8-14 days ago)
        (1, "Digit Reducer Fast", "c", "reducer.c", 9, "completed", 8.0, 10.0, 9.2, "Low Similarity", "Cleared"),
        (3, "Ledger Audit Implementation", "python", "ledger.py", 12, "completed", 44.0, 52.0, 48.8, "Medium Similarity", "Reviewed"),
        # Week 3 (15-21 days ago)
        (2, "Sequence Iterator", "javascript", "seq.js", 17, "completed", 14.0, 16.0, 15.2, "Low Similarity", "No Concern Identified"),
        # Week 4 (22-28 days ago)
        (1, "Initial Loop Algorithm", "python", "digits_v1.py", 24, "completed", 22.0, 26.0, 24.4, "Low Similarity", "Cleared"),
        # Week 5 (29-35 days ago)
        (3, "Basic Account Class", "java", "Account.java", 31, "completed", 50.0, 62.0, 57.2, "Medium Similarity", "Reviewed"),
        # Week 6 (36-42 days ago)
        (2, "Naive Fibonacci Loop", "python", "fib_naive.py", 38, "completed", 6.0, 8.0, 7.2, "Low Similarity", "Cleared"),
        (1, "Benchmark Test Harness", "c", "test_bench.c", 41, "completed", 11.0, 13.0, 12.2, "Low Similarity", "Cleared")
    ]

    for asgn_id, title, lang, fname, days_ago, status, text_sim, ast_sim, comb_sim, label, rev_stat in submissions_data:
        sub_time = (now - timedelta(days=days_ago, hours=2, minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO student_submissions (student_id, assignment_id, title, programming_language, source_filename, source_code, analysis_status, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (stu_id, asgn_id, title, lang, fname, f"// Code for {title}\nint main() {{ return 0; }}", status, sub_time))
        sub_id = cursor.lastrowid

        if status == "completed":
            cursor.execute("""
                INSERT INTO analysis_results (submission_id, text_similarity_score, ast_similarity_score, combined_similarity_score, similarity_label, analysis_summary, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sub_id, text_sim, ast_sim, comb_sim, label, f"Automated screening completed with {comb_sim}% combined similarity.", sub_time))
            res_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO faculty_reviews (analysis_result_id, faculty_id, review_status, review_notes, reviewed_at)
                VALUES (?, 1, ?, 'Automated review note by instructor.', ?)
            """, (res_id, rev_stat, sub_time))

    # 5. Seed 5 Notifications for STU001 (3 unread, 2 read)
    notifs = [
        ("High Similarity Flagged on Assignment #2", "Submission 'Dynamic Fib Generator' shows 78.3% structural similarity against historical archive. Please review comparison details.", "warning", f"/student/submissions", 0, 1),
        ("Deadline Approaching: CS201 Assignment", "Assignment 'CS201: Digit Manipulation & Loop Algorithms' deadline is in less than 24 hours. Submit your finalized code.", "assignment", "/student/submit?assignment_id=1", 0, 4),
        ("Automated Screening In Progress", "Your submission 'Matrix Sequence Generator' is currently queued in the AST parser engine.", "system", "/student/submissions", 0, 12),
        ("Analysis Completed for CS302", "Submission 'Account Transaction Ledger' finished screening with 38.0% similarity (Medium band).", "info", "/student/submissions", 1, 24),
        ("Academic Integrity Guidelines Updated", "Please review the updated university policy on permitted algorithm discussions and open-source citations.", "info", "/student/academic-integrity", 1, 72)
    ]

    for title, msg, cat, link, is_read, hours_ago in notifs:
        n_time = (now - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO student_notifications (student_id, title, message, category, link_url, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (stu_id, title, msg, cat, link, is_read, n_time))

    conn.commit()
    conn.close()
    print("Seed complete! STU001 now has 12 submissions, 5 notifications, and calibrated test data.")

if __name__ == "__main__":
    seed_test_data()
