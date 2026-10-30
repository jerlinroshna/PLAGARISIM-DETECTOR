import unittest
from unittest.mock import patch, MagicMock
import json
import os
from app import create_app
import database
from services.grok_service import GrokService

class GrokIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

        # Ensure database tables and columns are up to date
        database.init_db()

        conn = database.get_db_connection()
        row = conn.execute("SELECT submission_id FROM analysis_results ORDER BY id ASC LIMIT 1").fetchone()
        self.sub_id = row["submission_id"] if row else 1
        conn.close()

    def test_missing_api_key_returns_clear_error(self):
        """When XAI_API_KEY is not set or empty, returns clear error and success=False."""
        with patch.dict(os.environ, {"XAI_API_KEY": ""}, clear=False):
            with patch("config.XAI_API_KEY", ""):
                result = GrokService.explain_submission(self.sub_id, force_refresh=True)
                self.assertFalse(result.get("success"))
                self.assertIn("API key is missing", result.get("error", ""))

    def test_evidence_extraction_privacy(self):
        """Verifies that extracted evidence omits student personal identity (name, username, id, email)
        and omits full source files, sending only required metrics and matched segments.
        """
        evidence = GrokService.extract_evidence_for_grok(self.sub_id)
        if evidence:
            # Must NOT contain personal identifier fields
            self.assertNotIn("student_name", evidence)
            self.assertNotIn("student_username", evidence)
            self.assertNotIn("student_id_string", evidence)
            self.assertNotIn("email", evidence)

            # Must contain verified plagiarism metrics
            self.assertIn("language", evidence)
            self.assertIn("combined_similarity_score", evidence)
            self.assertIn("text_similarity_score", evidence)
            self.assertIn("ast_similarity_score", evidence)
            self.assertIn("similarity_label", evidence)
            self.assertIn("matched_sections", evidence)

    def test_prompt_enforces_rules_and_metrics(self):
        """Verifies that generated prompts instruct Grok not to invent scores or make final accusations."""
        dummy_evidence = {
            "language": "python",
            "assignment_subject": "Data Structures",
            "assignment_topic": "Binary Search Trees",
            "student_total_lines": 40,
            "historical_total_lines": 45,
            "has_historical_match": True,
            "historical_academic_year": "2025",
            "historical_assignment": "Binary Search Trees",
            "text_similarity_score": 75.0,
            "ast_similarity_score": 88.0,
            "combined_similarity_score": 82.8,
            "similarity_label": "High Similarity",
            "analysis_summary": "High structural overlap in tree rotation algorithms.",
            "matched_blocks_count": 2,
            "matched_lines_count": 18,
            "matched_sections": [
                {
                    "student_lines": "Lines 10-18",
                    "historical_lines": "Lines 12-20",
                    "student_snippet": "def rotate_left(node):\n    pass",
                    "historical_snippet": "def rotate_left(node):\n    pass"
                }
            ]
        }
        sys_prompt, user_prompt = GrokService.build_prompts(dummy_evidence)

        # Enforce operational rules
        self.assertIn("ONLY explain the verified results", sys_prompt)
        self.assertIn("NEVER invent", sys_prompt)
        self.assertIn("DO NOT make the final plagiarism determination", sys_prompt)

        # Verified metrics in user prompt
        self.assertIn("82.8%", user_prompt)
        self.assertIn("75.0%", user_prompt)
        self.assertIn("88.0%", user_prompt)
        self.assertIn("High Similarity", user_prompt)

    @patch("services.grok_service.requests.post")
    def test_successful_grok_explanation_persists_to_db(self, mock_post):
        """Verifies that a valid xAI Grok response is returned and cached in the database."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "### 1. Executive Summary\nHigh structural similarity detected between code implementations."
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"XAI_API_KEY": "xai-test-key-12345"}):
            result = GrokService.explain_submission(self.sub_id, force_refresh=True)
            self.assertTrue(result.get("success"))
            self.assertIn("Executive Summary", result.get("explanation"))

            # Verify saved in database
            conn = database.get_db_connection()
            row = conn.execute("SELECT grok_explanation FROM analysis_results WHERE submission_id = ?", (self.sub_id,)).fetchone()
            conn.close()
            if row:
                self.assertIsNotNone(row["grok_explanation"])
                self.assertIn("Executive Summary", row["grok_explanation"])

    def test_faculty_only_access_control(self):
        """Verifies that non-faculty and unauthenticated users cannot trigger Grok explain endpoint."""
        # 1. Unauthenticated request should redirect to login
        res_unauth = self.client.post(f"/faculty/analysis/{self.sub_id}/explain", json={"refresh": True})
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn("/login", res_unauth.headers.get("Location", ""))

        # 2. Student role request should be denied
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "STU001"
            sess["role"] = "student"
            sess["full_name"] = "Student 001"

        res_student = self.client.post(f"/faculty/analysis/{self.sub_id}/explain", json={"refresh": True})
        self.assertIn(res_student.status_code, (302, 403))

    @patch("services.grok_service.requests.post")
    def test_faculty_explain_route_endpoint(self, mock_post):
        """Verifies that an authorized faculty user can call the explain endpoint and receive JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "### 1. Executive Summary\nCode logic matches historical implementation."
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "FAC001"
            sess["role"] = "faculty"
            sess["full_name"] = "Dr. Faculty"

        with patch.dict(os.environ, {"XAI_API_KEY": "xai-test-key-faculty"}):
            res = self.client.post(f"/faculty/analysis/{self.sub_id}/explain", json={"refresh": True})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("success"))
            self.assertIn("Executive Summary", data.get("explanation"))

    def test_comparison_page_renders_with_grok_button_and_detector_works(self):
        """Verifies that the faculty comparison page includes the Grok AI card and button,
        and that the plagiarism detector remains fully functional.
        """
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "FAC001"
            sess["role"] = "faculty"
            sess["full_name"] = "Dr. Faculty"

        res = self.client.get(f"/faculty/analysis/{self.sub_id}")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("btn-explain-grok", html)
        self.assertIn("Grok AI Analysis & Interpretation", html)
        self.assertIn("Side-by-Side Source Code Inspection", html)
        self.assertIn("Combined Plagiarism Score", html)

if __name__ == "__main__":
    unittest.main()
