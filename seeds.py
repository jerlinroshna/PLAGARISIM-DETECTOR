import csv
import os
from werkzeug.security import generate_password_hash
from datetime import datetime
import config
from database import get_db_connection

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

    # Dedicated demo student account (demo_student)
    cursor.execute("SELECT id FROM users WHERE username = 'demo_student'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, role, email) VALUES (?, ?, ?, ?, ?)",
            ("demo_student", student_pw_hash, "Demo Student", "student", "demo_student@college.edu")
        )
    csv_rows.append(["demo_student", "Demo Student", "student", "Student@123"])

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
    except Exception:
        pass

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
        """, [(f"STU{idx+1:03d}", h[0], h[1], h[2], h[3], h[4], h[5], "[DEMO] " + h[6], 1, h[7]) for idx, h in enumerate(historical_samples)])

    # Ensure all demo records have student_id populated with student usernames
    cursor.execute("""
        UPDATE historical_submissions 
        SET student_id = printf('STU%03d', id)
        WHERE student_id IS NULL OR student_id = '' OR student_id LIKE 'DEMO-HIST-%'
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


def seed_sample_student_submissions():
    """Seeds realistic, clearly identifiable demo submissions and reports for the designated demo student accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find candidate demo student accounts: 'demo_student' and 'STU001'
    cursor.execute("SELECT id, username FROM users WHERE username IN ('demo_student', 'STU001')")
    demo_students = cursor.fetchall()
    if not demo_students:
        conn.close()
        return

    # Helper for relative dates across past 6 calendar months
    now = datetime.now()
    def get_month_date(months_ago, day=15, hour=14, minute=30):
        year = now.year
        month = now.month - months_ago
        while month <= 0:
            month += 12
            year -= 1
        if month == 2 and day > 28:
            day = 28
        elif day > 30 and month in (4, 6, 9, 11):
            day = 30
        dt = datetime(year, month, day, hour, minute, 0)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    # Get sample assignments (first 4)
    assignments = cursor.execute("SELECT id FROM assignments ORDER BY id ASC LIMIT 4").fetchall()
    asgn_ids = [a["id"] for a in assignments] if assignments else [1, 2, 3, 4]
    a1 = asgn_ids[0] if len(asgn_ids) > 0 else 1
    a2 = asgn_ids[1] if len(asgn_ids) > 1 else a1
    a3 = asgn_ids[2] if len(asgn_ids) > 2 else a1
    a4 = asgn_ids[3] if len(asgn_ids) > 3 else a1

    # Get historical submission IDs for matching
    hist_rows = cursor.execute("SELECT id FROM historical_submissions ORDER BY id ASC LIMIT 6").fetchall()
    hist_ids = [h["id"] for h in hist_rows] if hist_rows else [1, 2, 3, 4, 5, 6]
    h1 = hist_ids[0] if len(hist_ids) > 0 else None
    h2 = hist_ids[1] if len(hist_ids) > 1 else h1
    h3 = hist_ids[2] if len(hist_ids) > 2 else h1
    h4 = hist_ids[3] if len(hist_ids) > 3 else h1
    h5 = hist_ids[4] if len(hist_ids) > 4 else h1

    # Get a faculty user id for reviews
    faculty_row = cursor.execute("SELECT id FROM users WHERE role = 'faculty' LIMIT 1").fetchone()
    fac_id = faculty_row["id"] if faculty_row else 1

    # Define the 8 realistic demo submissions
    # Format: (asgn_id, title, lang, filename, code, status, submitted_at, sim_result, faculty_review)
    demo_specs = [
        # 1. 0-20% Low Similarity (C, Asgn 1, Month -5)
        (
            a1,
            "[DEMO] Iterative Digit Extraction & Counter",
            "c",
            "digit_counter.c",
            """#include <stdio.h>

int count_digits_and_sum(int n, int *out_sum) {
    int count = 0, sum = 0;
    int temp = n > 0 ? n : -n;
    while (temp > 0) {
        sum += (temp % 10);
        temp /= 10;
        count++;
    }
    *out_sum = sum;
    return count;
}

int main() {
    int num = 45892, s = 0;
    int c = count_digits_and_sum(num, &s);
    printf("Digits: %d, Sum: %d\\n", c, s);
    return 0;
}""",
            "completed",
            get_month_date(5, 12, 10, 15),
            {
                "hist_id": h1,
                "text_score": 12.0,
                "ast_score": 15.6,
                "comb_score": 14.2,
                "label": "Low Similarity",
                "summary": "Original control flow structure with low token overlap against institutional archives."
            },
            {
                "status": "Cleared",
                "notes": "Verified independent algorithm logic. No similarity concerns."
            }
        ),

        # 2. 21-40% Low Similarity (Python, Asgn 2, Month -4)
        (
            a2,
            "[DEMO] Sequence Generator & Term Display",
            "python",
            "fib_generator.py",
            """def generate_fibonacci_sequence(limit):
    \"\"\"Generates the first n numbers of the Fibonacci sequence iteratively.\"\"\"
    if limit <= 0:
        return []
    sequence = [0]
    if limit == 1:
        return sequence
    sequence.append(1)
    for _ in range(2, limit):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence

if __name__ == '__main__':
    n = 10
    print(f'First {n} Fibonacci numbers: {generate_fibonacci_sequence(n)}')""",
            "completed",
            get_month_date(4, 18, 14, 20),
            {
                "hist_id": h3,
                "text_score": 26.5,
                "ast_score": 29.8,
                "comb_score": 28.5,
                "label": "Low Similarity",
                "summary": "Standard algorithmic idiom detected with acceptable unique variable scoping."
            },
            {
                "status": "Cleared",
                "notes": "Standard programming exercise pattern. Approved."
            }
        ),

        # 3. 41-60% Medium Similarity (Java, Asgn 3, Month -3)
        (
            a3,
            "[DEMO] Account Balance Management & Ledger",
            "java",
            "BankAccount.java",
            """public class BankAccount {
    private String accountId;
    private double balance;

    public BankAccount(String accountId, double initialDeposit) {
        this.accountId = accountId;
        this.balance = Math.max(0.0, initialDeposit);
    }

    public synchronized boolean deposit(double amount) {
        if (amount <= 0) return false;
        this.balance += amount;
        return true;
    }

    public synchronized boolean withdraw(double amount) {
        if (amount > 0 && amount <= this.balance) {
            this.balance -= amount;
            return true;
        }
        return false;
    }

    public double getBalance() {
        return this.balance;
    }
}""",
            "completed",
            get_month_date(3, 20, 16, 45),
            {
                "hist_id": h4,
                "text_score": 51.2,
                "ast_score": 55.8,
                "comb_score": 54.0,
                "label": "Medium Similarity",
                "summary": "Moderate AST branch alignment observed in deposit/withdraw synchronization blocks."
            },
            {
                "status": "Reviewed",
                "notes": "Class structure follows standard textbook pattern. Acceptable."
            }
        ),

        # 4. 61-80% High Similarity (Python, Asgn 4, Month -2)
        (
            a4,
            "[DEMO] String Tokenizer & Bi-directional Slicer",
            "python",
            "palindrome_slicer.py",
            """import re

def is_valid_palindrome(phrase: str) -> bool:
    \"\"\"Strips non-alphanumeric characters and checks palindrome symmetry.\"\"\"
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', phrase).lower()
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        right -= 1
    return True

if __name__ == '__main__':
    test_phrase = 'A man, a plan, a canal: Panama'
    print('Is palindrome:', is_valid_palindrome(test_phrase))""",
            "completed",
            get_month_date(2, 8, 11, 10),
            {
                "hist_id": h5,
                "text_score": 68.4,
                "ast_score": 75.7,
                "comb_score": 72.8,
                "label": "High Similarity",
                "summary": "High token and AST similarity with historical archive sample. Variable renaming detected."
            },
            {
                "status": "Under Investigation",
                "notes": "Structural similarity exceeds threshold. Student clarification requested."
            }
        ),

        # 5. 81-100% High Similarity (Java, Asgn 3, Month -2)
        (
            a3,
            "[DEMO] Banking Transaction & Concurrency Model",
            "java",
            "TransactionLedger.java",
            """public class TransactionLedger {
    private final String accountHolder;
    private double balance;

    public TransactionLedger(String holder, double openingBalance) {
        this.accountHolder = holder;
        this.balance = openingBalance;
    }

    public void processTransaction(String type, double amount) {
        if ("DEPOSIT".equalsIgnoreCase(type) && amount > 0) {
            this.balance += amount;
        } else if ("WITHDRAW".equalsIgnoreCase(type) && amount <= this.balance) {
            this.balance -= amount;
        }
    }

    public double queryBalance() {
        return this.balance;
    }
}""",
            "completed",
            get_month_date(2, 24, 15, 30),
            {
                "hist_id": h4,
                "text_score": 86.2,
                "ast_score": 91.5,
                "comb_score": 89.4,
                "label": "High Similarity",
                "summary": "Substantial structural isomorphism with AY 2023-24 archive record across method signatures."
            },
            {
                "status": "Violation Confirmed",
                "notes": "Direct structural copy of reference implementation without attribution."
            }
        ),

        # 6. Active: Processing (Python, Asgn 2, Month -1)
        (
            a2,
            "[DEMO] Optimized Fibonacci Matrix Exponentiation",
            "python",
            "matrix_fib.py",
            """def matrix_mult_2x2(A, B):
    return [
        [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
        [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]
    ]

def fast_fibonacci(n):
    if n <= 0: return 0
    return 1""",
            "processing",
            get_month_date(1, 19, 17, 0),
            None,
            None
        ),

        # 7. Active: Pending (C, Asgn 1, Current Month)
        (
            a1,
            "[DEMO] Pointer Arithmetic & Memory Buffer",
            "c",
            "memory_buffer.c",
            """#include <stdio.h>
#include <stdlib.h>

void reverse_buffer(int *arr, int len) {
    int *start = arr;
    int *end = arr + len - 1;
    while (start < end) {
        int temp = *start;
        *start = *end;
        *end = temp;
        start++;
        end--;
    }
}""",
            "pending",
            get_month_date(0, min(now.day, 20), 9, 30),
            None,
            None
        ),

        # 8. Failed: Compilation error (Java, Asgn 3, Current Month)
        (
            a3,
            "[DEMO] Multi-threaded Transaction Queue",
            "java",
            "FaultyQueue.java",
            """public class FaultyQueue {
    // Missing closing brace causes deliberate compilation failure
    public void enqueue(String s) {
""",
            "failed",
            get_month_date(0, max(1, now.day - 1), 16, 45),
            None,
            None
        )
    ]

    for student in demo_students:
        stu_id = student["id"]
        # Check if demo submissions already exist for this student to prevent duplicate insertions
        existing_demo = cursor.execute(
            "SELECT COUNT(*) FROM student_submissions WHERE student_id = ? AND title LIKE '[DEMO]%'",
            (stu_id,)
        ).fetchone()[0]

        if existing_demo > 0:
            continue  # Already seeded for this demo student

        for asgn_id, title, lang, fname, code, status, sub_date, sim_res, fac_rev in demo_specs:
            cursor.execute("""
                INSERT INTO student_submissions
                (student_id, assignment_id, title, programming_language, source_filename, source_code, analysis_status, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (stu_id, asgn_id, title, lang, fname, code, status, sub_date))
            sub_id = cursor.lastrowid

            if sim_res and status == "completed":
                cursor.execute("""
                    INSERT INTO analysis_results
                    (submission_id, matched_historical_id, text_similarity_score, ast_similarity_score, combined_similarity_score, similarity_label, analysis_summary, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sub_id,
                    sim_res["hist_id"],
                    sim_res["text_score"],
                    sim_res["ast_score"],
                    sim_res["comb_score"],
                    sim_res["label"],
                    sim_res["summary"],
                    sub_date
                ))
                res_id = cursor.lastrowid

                if fac_rev:
                    cursor.execute("""
                        INSERT INTO faculty_reviews
                        (analysis_result_id, faculty_id, review_status, review_notes, reviewed_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        res_id,
                        fac_id,
                        fac_rev["status"],
                        fac_rev["notes"],
                        sub_date
                    ))

    conn.commit()
    conn.close()
