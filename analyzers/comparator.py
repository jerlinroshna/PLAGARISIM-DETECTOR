import json
import sqlite3
from typing import Dict, Any, Optional, List
import config
import database
from analyzers.text_analyzer import TextAnalyzer
from analyzers.ast_python import PythonASTAnalyzer
from analyzers.ast_java import JavaASTAnalyzer
from analyzers.ast_javascript import JavaScriptASTAnalyzer
from analyzers.ast_c_cpp import CCppASTAnalyzer

class CodeComparator:
    """Orchestrates multi-language text and AST structural comparisons

    between student submissions and historical submissions.
    """

    @staticmethod
    def get_ast_analyzer(language: str):
        lang = language.lower()
        if lang == "python":
            return PythonASTAnalyzer()
        elif lang == "java":
            return JavaASTAnalyzer()
        elif lang == "javascript":
            return JavaScriptASTAnalyzer()
        elif lang in ("c", "cpp"):
            return CCppASTAnalyzer(lang)
        return None

    @classmethod
    def compare_code_pair(cls, code_a: str, code_b: str, language: str) -> Dict[str, Any]:
        """Performs isolated text and AST comparison between two code snippets."""
        text_result = TextAnalyzer.compute_similarity(code_a, code_b, language)
        ast_analyzer = cls.get_ast_analyzer(language)

        if ast_analyzer:
            ast_result = ast_analyzer.compute_similarity(code_a, code_b)
            if ast_result.get("success", False):
                ast_score = ast_result.get("score", 0.0)
                ast_summary = ast_result.get("summary", "")
                combined_score = round(config.WEIGHT_TEXT * text_result["score"] + config.WEIGHT_AST * ast_score, 2)
            else:
                # AST had a limitation or syntax error
                ast_score = 0.0
                ast_summary = ast_result.get("summary", "AST parser encountered an error.")
                # When AST fails due to syntax error, report partial text score and note error
                combined_score = round(text_result["score"], 2)
        else:
            ast_score = 0.0
            ast_result = {"success": False, "summary": f"No AST parser available for {language}."}
            ast_summary = ast_result["summary"]
            combined_score = round(text_result["score"], 2)

        # Label classification
        if combined_score >= config.THRESHOLD_HIGH:
            label = "High Similarity"
        elif combined_score >= config.THRESHOLD_MEDIUM:
            label = "Medium Similarity"
        else:
            label = "Low Similarity"

        return {
            "text_score": text_result["score"],
            "ast_score": ast_score,
            "combined_score": combined_score,
            "similarity_label": label,
            "matching_spans": text_result.get("matching_spans", []),
            "text_summary": text_result.get("summary", ""),
            "ast_summary": ast_summary,
            "ast_result": ast_result
        }

    @classmethod
    def analyze_submission(cls, submission_id: int) -> Dict[str, Any]:
        """Fetches submission, queries historical candidates, computes similarity,

        and persists results and evidence to SQLite.
        """
        conn = database.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.id, s.student_id, s.assignment_id, s.title, s.programming_language, 
                   s.source_filename, s.source_code, a.title AS assignment_title, a.subject
            FROM student_submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.id = ?
        """, (submission_id,))
        sub_row = cursor.fetchone()

        if not sub_row:
            conn.close()
            return {"success": False, "error": "Submission not found."}

        student_code = sub_row["source_code"]
        lang = sub_row["programming_language"].lower()
        asgn_title = sub_row["assignment_title"]
        asgn_subject = sub_row["subject"]

        # Step 1: Find relevant historical submissions
        # First preference: same assignment title and same language across any academic year
        cursor.execute("""
            SELECT id, academic_year, subject, assignment_name, programming_language,
                   source_filename, source_code, batch_label
            FROM historical_submissions
            WHERE LOWER(programming_language) = ? AND assignment_name = ?
            ORDER BY academic_year DESC
        """, (lang, asgn_title))
        historical_candidates = cursor.fetchall()

        # Second preference: same subject and same language if no assignment-specific records
        if not historical_candidates:
            cursor.execute("""
                SELECT id, academic_year, subject, assignment_name, programming_language,
                       source_filename, source_code, batch_label
                FROM historical_submissions
                WHERE LOWER(programming_language) = ? AND subject = ?
                ORDER BY academic_year DESC
            """, (lang, asgn_subject))
            historical_candidates = cursor.fetchall()

        # Third preference: any historical record in the same programming language
        if not historical_candidates:
            cursor.execute("""
                SELECT id, academic_year, subject, assignment_name, programming_language,
                       source_filename, source_code, batch_label
                FROM historical_submissions
                WHERE LOWER(programming_language) = ?
                ORDER BY academic_year DESC
            """, (lang,))
            historical_candidates = cursor.fetchall()

        # If still no historical candidates found
        if not historical_candidates:
            summary = "No comparable historical submissions found."
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_results 
                (submission_id, matched_historical_id, text_similarity_score, ast_similarity_score, combined_similarity_score, similarity_label, analysis_summary)
                VALUES (?, NULL, 0.0, 0.0, 0.0, 'Low Similarity', ?)
            """, (submission_id, summary))
            
            # Update submission status
            cursor.execute("UPDATE student_submissions SET analysis_status = 'completed' WHERE id = ?", (submission_id,))
            conn.commit()
            conn.close()

            return {
                "success": True,
                "submission_id": submission_id,
                "matched_historical_id": None,
                "text_score": 0.0,
                "ast_score": 0.0,
                "combined_score": 0.0,
                "similarity_label": "Low Similarity",
                "summary": summary,
                "matching_spans": []
            }

        # Step 2: Compare against all historical candidates to find highest match
        best_match = None
        best_score = -1.0
        best_comparison = None

        for hist in historical_candidates:
            comp = cls.compare_code_pair(student_code, hist["source_code"], lang)
            if comp["combined_score"] > best_score:
                best_score = comp["combined_score"]
                best_match = hist
                best_comparison = comp

        summary_text = (
            f"Compared with historical record '{best_match['source_filename']}' "
            f"(AY {best_match['academic_year']}, {best_match['assignment_name']}). "
            f"Text: {best_comparison['text_score']}%, AST Structural: {best_comparison['ast_score']}%. "
            f"{best_comparison['ast_summary']}"
        )

        # Step 3: Persist analysis_results
        cursor.execute("""
            INSERT OR REPLACE INTO analysis_results 
            (submission_id, matched_historical_id, text_similarity_score, ast_similarity_score, 
             combined_similarity_score, similarity_label, analysis_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id,
            best_match["id"],
            best_comparison["text_score"],
            best_comparison["ast_score"],
            best_comparison["combined_score"],
            best_comparison["similarity_label"],
            summary_text
        ))

        cursor.execute("SELECT id FROM analysis_results WHERE submission_id = ?", (submission_id,))
        result_id = cursor.fetchone()["id"]

        # Step 4: Persist matched_evidence
        cursor.execute("DELETE FROM matched_evidence WHERE analysis_result_id = ?", (result_id,))
        matching_spans = best_comparison["matching_spans"]
        if matching_spans:
            student_lines = [[m["student_start"], m["student_end"]] for m in matching_spans]
            historical_lines = [[m["historical_start"], m["historical_end"]] for m in matching_spans]
            cursor.execute("""
                INSERT INTO matched_evidence 
                (analysis_result_id, student_code_lines, historical_code_lines, evidence_type, details)
                VALUES (?, ?, ?, 'token_and_text_match', ?)
            """, (
                result_id,
                json.dumps(student_lines),
                json.dumps(historical_lines),
                json.dumps(matching_spans)
            ))

        # Step 5: Ensure faculty_reviews record exists
        cursor.execute("SELECT id FROM faculty_reviews WHERE analysis_result_id = ?", (result_id,))
        if not cursor.fetchone():
            cursor.execute("""
                SELECT id FROM users WHERE role = 'faculty' LIMIT 1
            """)
            default_fac = cursor.fetchone()
            fac_id = default_fac["id"] if default_fac else 1
            cursor.execute("""
                INSERT INTO faculty_reviews (analysis_result_id, faculty_id, review_status, review_notes)
                VALUES (?, ?, 'Pending Review', 'Awaiting faculty evaluation.')
            """, (result_id, fac_id))

        cursor.execute("UPDATE student_submissions SET analysis_status = 'completed' WHERE id = ?", (submission_id,))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "submission_id": submission_id,
            "matched_historical_id": best_match["id"],
            "matched_historical_filename": best_match["source_filename"],
            "matched_historical_year": best_match["academic_year"],
            "text_score": best_comparison["text_score"],
            "ast_score": best_comparison["ast_score"],
            "combined_score": best_comparison["combined_score"],
            "similarity_label": best_comparison["similarity_label"],
            "summary": summary_text,
            "matching_spans": matching_spans
        }
