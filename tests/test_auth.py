import unittest
import os
import csv
from app import create_app
import database
from auth import authenticate_user

class AuthAndSecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_demo_accounts_seeded_counts(self):
        """Verifies exactly 60 student demo accounts and 20 faculty demo accounts are created."""
        conn = database.get_db_connection()
        students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
        faculty = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'faculty'").fetchone()[0]
        conn.close()

        self.assertEqual(students, 60, f"Expected 60 students, found {students}")
        self.assertEqual(faculty, 20, f"Expected 20 faculty, found {faculty}")

    def test_idempotent_seeding(self):
        """Verifies that calling init_db again does not duplicate accounts."""
        database.init_db()
        conn = database.get_db_connection()
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()

        self.assertEqual(total_users, 80, f"Expected 80 total users, found {total_users}")

    def test_student_and_faculty_authentication(self):
        """Verifies authentication for student and faculty with correct and incorrect passwords."""
        # STU001 login
        stu_user = authenticate_user("STU001", "Student@123")
        self.assertIsNotNone(stu_user)
        self.assertEqual(stu_user["role"], "student")
        self.assertEqual(stu_user["full_name"], "Student 001")

        # FAC001 login
        fac_user = authenticate_user("FAC001", "Faculty@123")
        self.assertIsNotNone(fac_user)
        self.assertEqual(fac_user["role"], "faculty")
        self.assertEqual(fac_user["full_name"], "Faculty 001")

        # Invalid password
        bad_user = authenticate_user("STU001", "WrongPassword")
        self.assertIsNone(bad_user)

    def test_demo_accounts_csv_generation(self):
        """Verifies that demo_accounts.csv is generated for testing without leaking password hashes."""
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "demo_accounts.csv")
        self.assertTrue(os.path.exists(csv_path), "demo_accounts.csv must exist in data directory")

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 80)
        # Verify columns
        self.assertIn("username", rows[0])
        self.assertIn("role", rows[0])
        self.assertIn("initial_demo_password", rows[0])
        self.assertNotIn("password_hash", rows[0])

    def test_role_based_access_control(self):
        """Verifies that students cannot access faculty-only endpoints."""
        # Log in as STU001
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "STU001"
            sess["full_name"] = "Student 001"
            sess["role"] = "student"

        # Attempt to access faculty dashboard
        response = self.client.get("/faculty/dashboard", follow_redirects=False)
        # Should redirect to student dashboard with access denied
        self.assertEqual(response.status_code, 302)
        self.assertIn("/student/dashboard", response.headers["Location"])

if __name__ == "__main__":
    unittest.main()
