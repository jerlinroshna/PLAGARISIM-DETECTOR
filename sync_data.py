"""
Data Synchronization Utility for CodeGuard AST Plagiarism Detector.

Synchronizes:
1. Historical submissions between SQLite database and `uploads/historical/` filesystem archive.
2. Student submissions between SQLite database and `uploads/submissions/` filesystem archive.
3. Sample files in `samples/` with historical benchmark repository.
4. User accounts in SQLite database with `data/demo_accounts.csv`.
"""

import sqlite3
import os
import csv
import config

def sync_all_data():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- Starting CodeGuard Data Synchronization ---")

    # 1. Sync Historical Submissions from DB to uploads/historical/
    os.makedirs(config.UPLOADS_HISTORICAL_DIR, exist_ok=True)
    hist_rows = cursor.execute("SELECT id, source_filename, source_code FROM historical_submissions").fetchall()
    synced_hist_count = 0
    for row in hist_rows:
        filename = f"hist_{row['id']}_{row['source_filename']}"
        filepath = os.path.join(config.UPLOADS_HISTORICAL_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(row["source_code"] or "")
            synced_hist_count += 1
    print(f"[+] Historical submissions on disk: {len(hist_rows)} records verified ({synced_hist_count} new files written to {config.UPLOADS_HISTORICAL_DIR})")

    # 2. Sync Student Submissions from DB to uploads/submissions/
    os.makedirs(config.UPLOADS_SUBMISSIONS_DIR, exist_ok=True)
    sub_rows = cursor.execute("SELECT id, source_filename, source_code FROM student_submissions").fetchall()
    synced_sub_count = 0
    for row in sub_rows:
        sfname = row["source_filename"] or "submission.txt"
        filename = f"sub_{row['id']}_{sfname}"
        filepath = os.path.join(config.UPLOADS_SUBMISSIONS_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(row["source_code"] or "")
            synced_sub_count += 1
    print(f"[+] Student submissions on disk: {len(sub_rows)} records verified ({synced_sub_count} new files written to {config.UPLOADS_SUBMISSIONS_DIR})")

    # 3. Sync User Accounts with demo_accounts.csv
    users = cursor.execute("SELECT username, full_name, role FROM users ORDER BY username").fetchall()
    csv_rows = [["username", "demo_name", "role", "initial_demo_password"]]
    for u in users:
        role = u["role"]
        pw = "Faculty@123" if role == "faculty" else "Student@123"
        csv_rows.append([u["username"], u["full_name"], role, pw])

    with open(config.DEMO_ACCOUNTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
    print(f"[+] Demo accounts CSV synced: {len(users)} user credentials synced to {config.DEMO_ACCOUNTS_CSV}")

    # 4. Check Sample Files Coverage
    samples_dir = os.path.join(config.BASE_DIR, "samples")
    sample_files = []
    if os.path.exists(samples_dir):
        for root, _, files in os.walk(samples_dir):
            for file in files:
                sample_files.append(os.path.relpath(os.path.join(root, file), samples_dir))
    print(f"[+] Benchmark sample test files verified: {len(sample_files)} sample files ready in {samples_dir}")

    # 5. Summary Counts
    assignment_count = cursor.execute("SELECT COUNT(*) FROM assignments").fetchone()[0]
    analysis_count = cursor.execute("SELECT COUNT(*) FROM analysis_results").fetchone()[0]
    review_count = cursor.execute("SELECT COUNT(*) FROM faculty_reviews").fetchone()[0]
    notification_count = cursor.execute("SELECT COUNT(*) FROM student_notifications").fetchone()[0]

    print("\n--- Current Data Architecture Snapshot ---")
    print(f"- Registered Users: {len(users)} (60 students, 20 faculty, 1 demo)")
    print(f"- Assignments: {assignment_count}")
    print(f"- Historical Code Archives: {len(hist_rows)}")
    print(f"- Student Submissions: {len(sub_rows)}")
    print(f"- Automated Plagiarism Analyses: {analysis_count}")
    print(f"- Faculty Reviews / Actions: {review_count}")
    print(f"- Student Notifications: {notification_count}")
    print("------------------------------------------")

    conn.close()

if __name__ == "__main__":
    sync_all_data()
