import sqlite3
import csv
import os
from werkzeug.security import generate_password_hash
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
        cursor.execute("ALTER TABLE historical_submissions ADD COLUMN student_id TEXT DEFAULT 'DEMO-HIST-001'")
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

def seed_demo_accounts():
    """Generates 60 student demo accounts and 20 faculty demo accounts without duplication."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if accounts already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    csv_rows = [["username", "demo_name", "role", "initial_demo_password"]]

    # 60 Student accounts (STU001 - STU060)
    student_pw_hash = generate_password_hash("Student@123")
    for i in range(1, 61):
        uname = f"STU{i:03d}"
        dname = f"Student {i:03d}"
        email = f"{uname.lower()}@college.edu"
        csv_rows.append([uname, dname, "student", "Student@123"])

        cursor.execute("SELECT id FROM users WHERE username = ?", (uname,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role, email) VALUES (?, ?, ?, ?, ?)",
                (uname, student_pw_hash, dname, "student", email)
            )

    # 20 Faculty accounts (FAC001 - FAC020)
    faculty_pw_hash = generate_password_hash("Faculty@123")
    for i in range(1, 21):
        uname = f"FAC{i:03d}"
        dname = f"Faculty {i:03d}"
        email = f"{uname.lower()}@college.edu"
        csv_rows.append([uname, dname, "faculty", "Faculty@123"])

        cursor.execute("SELECT id FROM users WHERE username = ?", (uname,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role, email) VALUES (?, ?, ?, ?, ?)",
                (uname, faculty_pw_hash, dname, "faculty", email)
            )

    conn.commit()
    conn.close()

    # Export demo accounts CSV for local development reference
    try:
        with open(config.DEMO_ACCOUNTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
    except Exception as e:
        print(f"Warning: Could not write demo accounts CSV: {e}")

def seed_sample_assignments_and_history():
    """Seeds starter assignments and labeled demo historical records for testing comparison."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if assignments already exist
    cursor.execute("SELECT COUNT(*) FROM assignments")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM users WHERE role = 'faculty' LIMIT 1")
        faculty_row = cursor.fetchone()
        faculty_id = faculty_row["id"] if faculty_row else 1

        sample_assignments = [
            (
                "CS201: Digit Manipulation & Loop Algorithms",
                "Data Structures & Algorithms",
                "Implement integer digit extraction, reversal, and sum computation using while loops.",
                "c,cpp,python",
                "2026-11-30 23:59:00",
                faculty_id,
                1
            ),
            (
                "CS301: Fibonacci & Sequence Generation",
                "Programming Paradigms",
                "Compute the nth Fibonacci number iteratively and print the sequence terms.",
                "python,java,javascript",
                "2026-12-15 23:59:00",
                faculty_id,
                1
            ),
            (
                "CS302: Bank Account Transaction Manager",
                "Object-Oriented Programming",
                "Create a class to model bank transactions, deposit, withdrawal, and balance checking.",
                "java,cpp,python",
                "2026-12-20 23:59:00",
                faculty_id,
                1
            ),
            (
                "CS401: String Tokenizer & Palindrome Checker",
                "Web & Scripting Technologies",
                "Process an input string, strip punctuation, and verify palindrome properties.",
                "javascript,python",
                "2026-12-25 23:59:00",
                faculty_id,
                1
            )
        ]

        cursor.executemany("""
            INSERT INTO assignments (title, subject, description, allowed_languages, deadline, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_assignments)

    # Check if historical submissions already exist
    cursor.execute("SELECT COUNT(*) FROM historical_submissions")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM users WHERE role = 'faculty' LIMIT 1")
        faculty_row = cursor.fetchone()
        faculty_id = faculty_row["id"] if faculty_row else 1

        # Clearly labeled historical demo records
        historical_samples = [
            # C Historical Sample 1 (Digit Manipulation)
            (
                "2023-2024",
                "Data Structures & Algorithms",
                "CS201: Digit Manipulation & Loop Algorithms",
                "c",
                "hist_digit_sum_2023.c",
                """#include <stdio.h>

int main() {
    int num, temp, sum = 0, rem;
    printf("Enter number: ");
    scanf("%d", &num);
    temp = num;
    while (temp > 0) {
        rem = temp % 10;
        sum = sum + rem;
        temp = temp / 10;
    }
    printf("Sum of digits = %d\\n", sum);
    return 0;
}""",
                "Demo Data - Past Year Archive (AY 2023-24)",
                faculty_id
            ),
            # C Historical Sample 2 (Item Price Calculation)
            (
                "2022-2023",
                "Data Structures & Algorithms",
                "CS201: Digit Manipulation & Loop Algorithms",
                "c",
                "hist_billing_2022.c",
                """#include <stdio.h>

int main() {
    int a, b, c;
    int p, n, pen, total;
    scanf("%d %d %d", &a, &b, &c);
    p = a * 20;
    n = b * 70;
    pen = c * 9;
    total = p + n + pen;
    printf("%d\\n", total);
    return 0;
}""",
                "Demo Data - Past Year Archive (AY 2022-23)",
                faculty_id
            ),
            # Python Historical Sample (Fibonacci)
            (
                "2023-2024",
                "Programming Paradigms",
                "CS301: Fibonacci & Sequence Generation",
                "python",
                "hist_fibonacci_2023.py",
                """def compute_fibonacci(limit):
    first = 0
    second = 1
    sequence = []
    for step in range(limit):
        sequence.append(first)
        next_val = first + second
        first = second
        second = next_val
    return sequence

def main():
    n = int(input("Terms: "))
    result = compute_fibonacci(n)
    print("Sequence:", result)

if __name__ == "__main__":
    main()
""",
                "Demo Data - Past Year Archive (AY 2023-24)",
                faculty_id
            ),
            # Java Historical Sample (Bank Account)
            (
                "2023-2024",
                "Object-Oriented Programming",
                "CS302: Bank Account Transaction Manager",
                "java",
                "HistBankAccount2023.java",
                """public class Account {
    private double balance;
    private String accountNumber;

    public Account(String accNum, double initialBalance) {
        this.accountNumber = accNum;
        this.balance = initialBalance;
    }

    public void deposit(double amount) {
        if (amount > 0) {
            this.balance += amount;
        }
    }

    public boolean withdraw(double amount) {
        if (amount > 0 && amount <= this.balance) {
            this.balance -= amount;
            return true;
        }
        return false;
    }

    public double getBalance() {
        return this.balance;
    }
}
""",
                "Demo Data - Past Year Archive (AY 2023-24)",
                faculty_id
            ),
            # JavaScript Historical Sample (Palindrome)
            (
                "2024-2025",
                "Web & Scripting Technologies",
                "CS401: String Tokenizer & Palindrome Checker",
                "javascript",
                "hist_palindrome_2024.js",
                """function isPalindrome(text) {
    let cleaned = text.toLowerCase().replace(/[^a-z0-9]/g, '');
    let len = cleaned.length;
    for (let i = 0; i < len / 2; i++) {
        if (cleaned[i] !== cleaned[len - 1 - i]) {
            return false;
        }
    }
    return true;
}

const input = "racecar";
console.log(isPalindrome(input));
""",
                "Demo Data - Past Year Archive (AY 2024-25)",
                faculty_id
            ),
            # C++ Historical Sample (Fibonacci / Matrix)
            (
                "2023-2024",
                "Programming Paradigms",
                "CS301: Fibonacci & Sequence Generation",
                "cpp",
                "hist_fibonacci_2023.cpp",
                """#include <iostream>
#include <vector>

void generateFibonacci(int n) {
    long long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        std::cout << a << " ";
        long long next = a + b;
        a = b;
        b = next;
    }
    std::cout << std::endl;
}

int main() {
    int count;
    std::cin >> count;
    generateFibonacci(count);
    return 0;
}
""",
                "Demo Data - Past Year Archive (AY 2023-24)",
                faculty_id
            )
        ]

        cursor.executemany("""
            INSERT INTO historical_submissions 
            (student_id, academic_year, subject, assignment_name, programming_language, source_filename, source_code, batch_label, is_authorized_for_students, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [("DEMO-HIST-STU" + str(idx+1), h[0], h[1], h[2], h[3], h[4], h[5], "[DEMO] " + h[6], 1, h[7]) for idx, h in enumerate(historical_samples)])

    # Ensure all demo records have student_id populated and clearly labeled
    cursor.execute("""
        UPDATE historical_submissions 
        SET student_id = 'DEMO-HIST-STU' || id 
        WHERE student_id IS NULL OR student_id = '' OR student_id = 'DEMO-HIST-001'
    """)

    conn.commit()
    conn.close()

def seed_sample_notifications():
    """Seeds helpful initial notifications for student demo accounts if none exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check student accounts
    students = cursor.execute("SELECT id, username FROM users WHERE role = 'student'").fetchall()
    cursor.execute("UPDATE student_notifications SET link_url = '/student/dashboard' WHERE link_url = '/student/academic-integrity'")
    for stu in students[:5]:  # seed for top 5 demo students
        existing = cursor.execute("SELECT COUNT(*) FROM student_notifications WHERE student_id = ?", (stu["id"],)).fetchone()[0]
        if existing == 0:
            sample_notifs = [
                ("Academic Session 2024–2025 Active", "Welcome to the Academic Integrity & Code Submission Portal. Please review the submission guidelines before submitting your assignments.", "info", "/student/dashboard"),
                ("Data Structures Lab 1 Open", "Assignment 'Data Structures Lab 1' is currently active and accepting submissions in Java, Python, and C++.", "assignment", "/student/submit"),
                ("Automated Screening Engine Ready", "Multi-language AST structural screening (Python, C, C++, Java, JS) is fully operational for this academic session.", "system", "/student/dashboard")
            ]
            for title, msg, cat, link in sample_notifs:
                cursor.execute("""
                    INSERT INTO student_notifications (student_id, title, message, category, link_url, is_read)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (stu["id"], title, msg, cat, link))

    conn.commit()
    conn.close()
