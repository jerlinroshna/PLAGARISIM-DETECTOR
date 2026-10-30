import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import database

logger = logging.getLogger(__name__)

def extract_submission_evidence(submission_id: int) -> Optional[Dict[str, Any]]:
    """Extracts strictly necessary algorithmic evidence for Grok.
    Excludes personal student data (username, full name, student ID, email)
    and excludes full source files to preserve student privacy and token efficiency.
    """
    conn = database.get_db_connection()
    try:
        sub = conn.execute("""
            SELECT s.id, s.programming_language, s.source_code,
                   a.title AS assignment_title, a.subject
            FROM student_submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.id = ?
        """, (submission_id,)).fetchone()

        if not sub:
            return None

        result = conn.execute("""
            SELECT r.id, r.matched_historical_id, r.text_similarity_score, r.ast_similarity_score,
                   r.combined_similarity_score, r.similarity_label, r.analysis_summary,
                   h.academic_year, h.subject AS hist_subject, h.assignment_name AS hist_assignment,
                   h.source_code AS hist_source_code
            FROM analysis_results r
            LEFT JOIN historical_submissions h ON r.matched_historical_id = h.id
            WHERE r.submission_id = ?
        """, (submission_id,)).fetchone()

        if not result:
            return None

        evidence_rows = conn.execute("""
            SELECT student_code_lines, historical_code_lines, details
            FROM matched_evidence
            WHERE analysis_result_id = ?
        """, (result["id"],)).fetchall()

        # Process matched segments safely
        student_code_lines = sub["source_code"].splitlines()
        hist_code_lines = (result["hist_source_code"] or "").splitlines()

        matched_spans_extracted = []
        matched_line_count = 0

        for ev in evidence_rows:
            if ev["details"]:
                try:
                    spans = json.loads(ev["details"])
                    for span in spans:
                        s_start = span.get("student_start", 1)
                        s_end = span.get("student_end", 1)
                        h_start = span.get("historical_start", 1)
                        h_end = span.get("historical_end", 1)
                        matched_line_count += max(0, s_end - s_start + 1)

                        s_excerpt = "\n".join(student_code_lines[s_start - 1 : min(s_end, s_start + 9)])
                        h_excerpt = "\n".join(hist_code_lines[h_start - 1 : min(h_end, h_start + 9)]) if hist_code_lines else ""

                        matched_spans_extracted.append({
                            "student_lines": f"Lines {s_start}-{s_end}",
                            "historical_lines": f"Lines {h_start}-{h_end}",
                            "student_snippet": s_excerpt,
                            "historical_snippet": h_excerpt
                        })
                except Exception as e:
                    logger.warning("Error parsing matched span details: %s", e)

        # Limit to top 5 representative spans
        matched_spans_extracted = matched_spans_extracted[:5]

        return {
            "submission_id": sub["id"],
            "language": sub["programming_language"],
            "programming_language": sub["programming_language"],
            "assignment_subject": sub["subject"],
            "assignment_topic": sub["assignment_title"],
            "assignment_title": sub["assignment_title"],
            "subject": sub["subject"],
            "student_total_lines": len(student_code_lines),
            "historical_total_lines": len(hist_code_lines) if hist_code_lines else 0,
            "has_historical_match": bool(result["matched_historical_id"]),
            "historical_academic_year": result["academic_year"] if result["matched_historical_id"] else None,
            "historical_assignment": result["hist_assignment"] if result["matched_historical_id"] else None,
            "text_similarity_score": round(result["text_similarity_score"] or 0.0, 1),
            "ast_similarity_score": round(result["ast_similarity_score"] or 0.0, 1),
            "combined_similarity_score": round(result["combined_similarity_score"] or 0.0, 1),
            "similarity_label": result["similarity_label"] or "Low Similarity",
            "analysis_summary": result["analysis_summary"] or "Automated screening complete.",
            "matched_blocks_count": len(matched_spans_extracted),
            "matched_lines_count": matched_line_count,
            "matched_sections": matched_spans_extracted,
            "matched_sections_count": len(matched_spans_extracted),
            "matched_line_count": matched_line_count,
        }
    finally:
        conn.close()


def extract_report_evidence(submission_id: int, faculty_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Gathers full comprehensive case evidence for formal investigation report generation."""
    conn = database.get_db_connection()
    try:
        sub = conn.execute("""
            SELECT s.id, s.title, s.programming_language, s.source_filename,
                   s.source_code, s.submitted_at, s.analysis_status,
                   a.title AS assignment_title, a.subject
            FROM student_submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.id = ?
        """, (submission_id,)).fetchone()

        if not sub:
            return None

        result = conn.execute("""
            SELECT r.id, r.matched_historical_id, r.text_similarity_score,
                   r.ast_similarity_score, r.combined_similarity_score,
                   r.similarity_label, r.analysis_summary, r.grok_explanation,
                   h.academic_year, h.subject AS hist_subject,
                   h.assignment_name AS hist_assignment,
                   h.source_filename AS hist_filename,
                   h.source_code AS hist_source_code
            FROM analysis_results r
            LEFT JOIN historical_submissions h ON r.matched_historical_id = h.id
            WHERE r.submission_id = ?
        """, (submission_id,)).fetchone()

        if not result:
            return None

        review = conn.execute("""
            SELECT review_status, review_notes, reviewed_at
            FROM faculty_reviews
            WHERE analysis_result_id = ?
        """, (result["id"],)).fetchone()

        evidence_rows = conn.execute("""
            SELECT student_code_lines, historical_code_lines, details
            FROM matched_evidence
            WHERE analysis_result_id = ?
        """, (result["id"],)).fetchall()

        student_code = sub["source_code"] or ""
        student_lines = student_code.splitlines()
        hist_code = result["hist_source_code"] or ""
        hist_lines = hist_code.splitlines()

        matched_sections = []
        matched_lines_count = 0

        for ev in evidence_rows:
            if ev["details"]:
                try:
                    spans = json.loads(ev["details"])
                    for span in spans:
                        s_start = span.get("student_start", 1)
                        s_end = span.get("student_end", 1)
                        h_start = span.get("historical_start", 1)
                        h_end = span.get("historical_end", 1)
                        matched_lines_count += max(0, s_end - s_start + 1)

                        s_excerpt = "\n".join(student_lines[s_start - 1 : min(s_end, s_start + 15)])
                        h_excerpt = "\n".join(hist_lines[h_start - 1 : min(h_end, h_start + 15)]) if hist_lines else ""

                        matched_sections.append({
                            "student_lines": f"Lines {s_start}-{s_end}",
                            "historical_lines": f"Lines {h_start}-{h_end}",
                            "student_snippet": s_excerpt,
                            "historical_snippet": h_excerpt
                        })
                except Exception as e:
                    logger.warning("Error parsing span for report: %s", e)

        matched_sections = matched_sections[:6]
        generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        return {
            "submission_id": sub["id"],
            "generated_at": generated_at,
            "faculty_name": faculty_user.get("full_name", "Faculty Member"),
            "faculty_username": faculty_user.get("username", "FACULTY"),
            "assignment_title": sub["assignment_title"] or "N/A",
            "subject": sub["subject"] or "N/A",
            "language": sub["programming_language"] or "N/A",
            "submitted_at": sub["submitted_at"] or "N/A",
            "source_filename": sub["source_filename"] or f"submission_{sub['id']}.txt",
            "analysis_status": sub["analysis_status"] or "completed",
            "student_total_lines": len(student_lines),
            "text_score": round(result["text_similarity_score"] or 0.0, 1),
            "ast_score": round(result["ast_similarity_score"] or 0.0, 1),
            "combined_score": round(result["combined_similarity_score"] or 0.0, 1),
            "similarity_label": result["similarity_label"] or "Low Similarity",
            "analysis_summary": result["analysis_summary"] or "N/A",
            "has_historical_match": bool(result["matched_historical_id"]),
            "historical_academic_year": result["academic_year"],
            "historical_assignment": result["hist_assignment"],
            "hist_filename": result["hist_filename"],
            "historical_total_lines": len(hist_lines),
            "matched_sections": matched_sections,
            "matched_blocks_count": len(matched_sections),
            "matched_lines_count": matched_lines_count,
            "grok_explanation": result["grok_explanation"],
            "review_status": review["review_status"] if review else "Pending Review",
            "review_notes": review["review_notes"] if review and review["review_notes"] else "None recorded",
        }
    finally:
        conn.close()
