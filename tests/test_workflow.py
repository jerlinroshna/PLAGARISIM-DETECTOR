import unittest
from app import create_app
import database
from analyzers.comparator import CodeComparator

class WorkflowIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_end_to_end_student_submission_and_historical_matching(self):
        """Tests full pipeline: Student submits code -> Automated historical comparison runs ->

        Result generated -> Faculty reviews -> Student views own result.
        """
        # Step 1: Submit code as STU001
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "STU001"
            sess["full_name"] = "Student 001"
            sess["role"] = "student"

        # Submit C code similar to historical sample (CS201 Digit Manipulation)
        code_submission = """#include <stdio.h>
int main() {
    int n, t, s = 0, digit;
    printf("Enter val: ");
    scanf("%d", &n);
    t = n;
    while (t > 0) {
        digit = t % 10;
        s = s + digit;
        t = t / 10;
    }
    printf("Result: %d\\n", s);
    return 0;
}"""

        response = self.client.post("/student/submit", data={
            "assignment_id": 1,
            "title": "Digit Sum Implementation",
            "programming_language": "c",
            "code_text": code_submission
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Step 2: Verify in DB that submission and analysis exist
        conn = database.get_db_connection()
        sub = conn.execute(
            "SELECT id FROM student_submissions WHERE student_id = 1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        self.assertIsNotNone(sub)
        sub_id = sub["id"]

        result = conn.execute(
            "SELECT * FROM analysis_results WHERE submission_id = ?",
            (sub_id,)
        ).fetchone()
        self.assertIsNotNone(result)
        self.assertIsNotNone(result["matched_historical_id"])
        self.assertGreater(result["combined_similarity_score"], 60.0)
        self.assertIn(result["similarity_label"], ["Medium Similarity", "High Similarity"])

        # Step 3: Verify Student can view their OWN result
        student_view = self.client.get(f"/student/submission/{sub_id}")
        self.assertEqual(student_view.status_code, 200)
        self.assertIn(b"Submission Information", student_view.data)

        # Step 4: Verify Student 2 CANNOT view Student 1's submission (403 Forbidden)
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "STU002"
            sess["full_name"] = "Student 002"
            sess["role"] = "student"

        blocked_view = self.client.get(f"/student/submission/{sub_id}")
        self.assertEqual(blocked_view.status_code, 403)

        # Step 5: Faculty reviews the submission
        with self.client.session_transaction() as sess:
            sess["user_id"] = 61  # Faculty 001
            sess["username"] = "FAC001"
            sess["full_name"] = "Faculty 001"
            sess["role"] = "faculty"

        comparison_view = self.client.get(f"/faculty/analysis/{sub_id}")
        self.assertEqual(comparison_view.status_code, 200)
        self.assertIn(b"Side-by-Side Source Code Inspection", comparison_view.data)

        # Faculty saves review note
        review_post = self.client.post(f"/faculty/review/{sub_id}", data={
            "review_status": "Reviewed",
            "review_notes": "Algorithmic structure matches AY 2023-24 archive. Reviewed and acknowledged."
        }, follow_redirects=True)
        self.assertEqual(review_post.status_code, 200)

        # Verify review stored in DB
        rev = conn.execute(
            "SELECT * FROM faculty_reviews WHERE analysis_result_id = ?",
            (result["id"],)
        ).fetchone()
        self.assertEqual(rev["review_status"], "Reviewed")
        conn.close()

    def test_no_comparable_historical_submissions_found(self):
        """Verifies clear 'No comparable historical submissions found' message when no historical code exists."""
        conn = database.get_db_connection()
        # Create an assignment with an uncommon language with 0 historical submissions
        conn.execute("""
            INSERT INTO assignments (title, subject, allowed_languages, created_by, is_active)
            VALUES ('Unmatched Assignment', 'Unmatched Subject', 'javascript', 61, 1)
        """)
        asgn_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Insert a submission for this assignment but in an isolated language with no history
        conn.execute("""
            INSERT INTO student_submissions 
            (student_id, assignment_id, title, programming_language, source_filename, source_code, analysis_status)
            VALUES (1, ?, 'Test Isolated', 'unsupported_lang', 'test.xyz', 'some code', 'pending')
        """, (asgn_id,))
        sub_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        # Run comparator
        res = CodeComparator.analyze_submission(sub_id)
        self.assertEqual(res["summary"], "No comparable historical submissions found.")
        self.assertEqual(res["combined_score"], 0.0)

        # Clean up test assignment and submission
        conn = database.get_db_connection()
        conn.execute("DELETE FROM analysis_results WHERE submission_id = ?", (sub_id,))
        conn.execute("DELETE FROM student_submissions WHERE id = ?", (sub_id,))
        conn.execute("DELETE FROM assignments WHERE id = ?", (asgn_id,))
        conn.commit()
        conn.close()

    def test_csv_report_export(self):
        """Tests that faculty can download CSV report."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 61
            sess["username"] = "FAC001"
            sess["full_name"] = "Faculty 001"
            sess["role"] = "faculty"

        response = self.client.get("/faculty/reports/export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn(b"Submission ID,Student Username", response.data)

if __name__ == "__main__":
    unittest.main()
