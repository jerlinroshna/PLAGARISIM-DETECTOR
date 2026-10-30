import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import requests
import config
import database

logger = logging.getLogger(__name__)

class GrokService:
    """Service for interacting with the official xAI Grok API to provide evidence-grounded
    plagiarism analysis explanations for university faculty.
    """

    @classmethod
    def get_api_key(cls) -> str:
        """Reads xAI API key from environment variable XAI_API_KEY or config."""
        return (os.environ.get("XAI_API_KEY") or config.XAI_API_KEY or "").strip()

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if xAI API key is configured and non-empty."""
        return bool(cls.get_api_key())

    @classmethod
    def extract_evidence_for_grok(cls, submission_id: int) -> Optional[Dict[str, Any]]:
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

                            # Extract code excerpts for this span (max 10 lines per excerpt)
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

            # Limit to top 5 representative spans to keep tokens concise and focused
            matched_spans_extracted = matched_spans_extracted[:5]

            return {
                "submission_id": sub["id"],
                "language": sub["programming_language"],
                "assignment_subject": sub["subject"],
                "assignment_topic": sub["assignment_title"],
                "student_total_lines": len(student_code_lines),
                "historical_total_lines": len(hist_code_lines) if hist_code_lines else 0,
                "has_historical_match": bool(result["matched_historical_id"]),
                "historical_academic_year": result["academic_year"] if result["matched_historical_id"] else None,
                "historical_assignment": result["hist_assignment"] if result["matched_historical_id"] else None,
                "text_similarity_score": result["text_similarity_score"] or 0.0,
                "ast_similarity_score": result["ast_similarity_score"] or 0.0,
                "combined_similarity_score": result["combined_similarity_score"] or 0.0,
                "similarity_label": result["similarity_label"] or "Low Similarity",
                "analysis_summary": result["analysis_summary"] or "",
                "matched_blocks_count": len(matched_spans_extracted),
                "matched_lines_count": matched_line_count,
                "matched_sections": matched_spans_extracted
            }
        finally:
            conn.close()

    @classmethod
    def build_prompts(cls, evidence: Dict[str, Any]) -> Tuple[str, str]:
        """Constructs system and user prompts adhering to strict academic integrity guidelines."""
        system_prompt = (
            "You are Grok, an AI academic integrity expert assistant developed by xAI. "
            "Your objective is to provide a comprehensive, objective, and easy-to-understand explanation "
            "of automated source-code plagiarism analysis results for university faculty members.\n\n"
            "STRICT COMPLIANCE RULES:\n"
            "1. ONLY explain the verified results and evidence provided in the prompt. "
            "NEVER invent, hallucinate, modify, or recalculate any similarity percentages or metrics.\n"
            "2. DO NOT make the final plagiarism determination, accusation of cheating, or disciplinary judgment. "
            "Explicitly emphasize to faculty that similarity scores are decision-support indicators, "
            "and the final academic integrity determination rests entirely with the instructor.\n"
            "3. Clearly explain what the Text Similarity score measures (normalized token sequences, string matches, winnowing) "
            "vs what the AST Structural Similarity score measures (normalized Abstract Syntax Tree hierarchy, statement sequences, "
            "control flow, and identifier normalization which detects plagiarism even when variables and functions are renamed).\n"
            "4. Walk through what the matching code segments demonstrate and identify what structural or logic differences exist.\n"
            "5. Structure your output clearly using standard Markdown headings:\n"
            "   ### 1. Executive Summary\n"
            "   ### 2. Metric Breakdown: Text vs. AST Structural Similarity\n"
            "   ### 3. Matched Code Logic & Structural Evidence\n"
            "   ### 4. Code Differences & Distinguishing Logic\n"
            "   ### 5. Recommended Faculty Next Steps\n"
            "Be professional, clear, evidence-grounded, and concise."
        )

        user_content = [
            "Here is the verified plagiarism detection evidence computed by CodeGuard for faculty evaluation:\n",
            f"- **Programming Language**: {evidence['language'].upper()}",
            f"- **Course Subject**: {evidence['assignment_subject']}",
            f"- **Assignment Title**: {evidence['assignment_topic']}",
            f"- **Combined Plagiarism Score**: {evidence['combined_similarity_score']}% ({evidence['similarity_label']})",
            f"- **Formula Weighting**: 40% Text Similarity + 60% AST Structural Similarity",
            f"- **Text Similarity Score**: {evidence['text_similarity_score']}%",
            f"- **AST Structural Similarity Score**: {evidence['ast_similarity_score']}%",
            f"- **AST Engine Summary**: {evidence['analysis_summary']}",
            f"- **Student Submission Scope**: {evidence['student_total_lines']} total lines",
        ]

        if evidence['has_historical_match']:
            user_content.append(f"- **Matched Historical Reference**: Academic Year {evidence['historical_academic_year']} - '{evidence['historical_assignment']}' ({evidence['historical_total_lines']} total lines)")
            user_content.append(f"- **Total Matched Lines**: ~{evidence['matched_lines_count']} lines across {evidence['matched_blocks_count']} continuous block(s)")
            
            if evidence['matched_sections']:
                user_content.append("\n**Key Matched Code Sections:**")
                for i, sec in enumerate(evidence['matched_sections'], 1):
                    user_content.append(f"\n[Block {i}] Student ({sec['student_lines']}) vs Historical ({sec['historical_lines']}):")
                    user_content.append(f"Student code:\n```\n{sec['student_snippet']}\n```")
                    if sec['historical_snippet']:
                        user_content.append(f"Historical archive:\n```\n{sec['historical_snippet']}\n```")
            else:
                user_content.append("\nNo continuous multi-line code spans were recorded (structural/token similarity only).")
        else:
            user_content.append("- **Matched Historical Reference**: None found in repository for this subject/language.")

        user_content.append(
            "\nPlease explain these findings clearly for faculty, explaining the contrast between the text score "
            "and AST score, analyzing why these specific blocks matched, identifying differences, and providing guidance "
            "without making an accusation."
        )

        return system_prompt, "\n".join(user_content)

    @classmethod
    def call_xai_api(cls, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Calls the official xAI Grok chat completions endpoint with error handling."""
        api_key = cls.get_api_key()
        if not api_key:
            return {
                "success": False,
                "error": "xAI API key is missing. Set the XAI_API_KEY environment variable in your .env file or system environment to enable Grok AI explanations."
            }

        base_url = (os.environ.get("XAI_BASE_URL") or config.XAI_BASE_URL).rstrip("/")
        endpoint = f"{base_url}/chat/completions"
        model = os.environ.get("XAI_MODEL") or config.XAI_MODEL or "grok-2-latest"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1500
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    content = choices[0]["message"].get("content", "").strip()
                    return {
                        "success": True,
                        "explanation": content,
                        "model": model
                    }
                return {
                    "success": False,
                    "error": "Received an empty response from the xAI Grok API."
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "xAI API authentication failed (401 Unauthorized). Please check that your XAI_API_KEY is active and valid."
                }
            elif response.status_code == 429:
                return {
                    "success": False,
                    "error": "xAI API rate limit or quota exceeded (429). Please check your account usage on console.x.ai or try again shortly."
                }
            else:
                try:
                    err_json = response.json()
                    err_msg = err_json.get("error", {}).get("message") or err_json.get("message") or response.text
                except Exception:
                    err_msg = response.text
                return {
                    "success": False,
                    "error": f"xAI API error (HTTP {response.status_code}): {err_msg[:250]}"
                }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Connection to the xAI Grok API timed out (30s). Please check your connection and try again."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Failed to connect to the xAI Grok API endpoint. Please check your network connection."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error while communicating with xAI API: {str(e)}"
            }

    @classmethod
    def explain_submission(cls, submission_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Coordinates evidence collection, Grok API execution, and results caching."""
        # Check cache if not forcing refresh
        conn = database.get_db_connection()
        try:
            existing = conn.execute("""
                SELECT grok_explanation, grok_explained_at FROM analysis_results WHERE submission_id = ?
            """, (submission_id,)).fetchone()

            if existing and existing["grok_explanation"] and not force_refresh:
                return {
                    "success": True,
                    "explanation": existing["grok_explanation"],
                    "model": os.environ.get("XAI_MODEL") or config.XAI_MODEL,
                    "cached": True,
                    "explained_at": existing["grok_explained_at"]
                }
        finally:
            conn.close()

        evidence = cls.extract_evidence_for_grok(submission_id)
        if not evidence:
            return {
                "success": False,
                "error": f"Analysis results not found for submission #{submission_id}."
            }

        system_prompt, user_prompt = cls.build_prompts(evidence)
        result = cls.call_xai_api(system_prompt, user_prompt)

        if result.get("success"):
            # Persist explanation to database for future viewing
            conn = database.get_db_connection()
            try:
                conn.execute("""
                    UPDATE analysis_results 
                    SET grok_explanation = ?, grok_explained_at = CURRENT_TIMESTAMP
                    WHERE submission_id = ?
                """, (result["explanation"], submission_id))
                conn.commit()
            except Exception as e:
                logger.warning("Could not persist grok_explanation to DB: %s", e)
            finally:
                conn.close()

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # INVESTIGATION REPORT — long-form generation
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def build_report_prompts(cls, report_data: Dict[str, Any]) -> Tuple[str, str]:
        """Constructs the system and user prompts for a formal investigation report."""
        system_prompt = (
            "You are Grok, a senior academic integrity officer AI developed by xAI. "
            "You are generating a formal, structured ACADEMIC INTEGRITY INVESTIGATION REPORT "
            "for university faculty. This is an official document, not a chat message.\n\n"
            "STRICT RULES:\n"
            "1. Write in formal, professional language suitable for an official academic record.\n"
            "2. ONLY reference the exact numerical scores and evidence provided. NEVER invent or recalculate any metric.\n"
            "3. DO NOT make a final plagiarism determination or accusation. State that the final determination rests with the instructor.\n"
            "4. Follow the EXACT 7-section structure specified in the user prompt. Use the exact heading names.\n"
            "5. Each section must be substantive (3-6 sentences minimum). Section 4 must reference specific code block evidence.\n"
            "6. Use markdown formatting (## headings, **bold**, bullet lists, code blocks).\n"
            "7. Section 7 must include the mandatory disclaimer verbatim as instructed.\n"
            "Generate a thorough, evidence-grounded document that faculty can use as a formal case file."
        )

        ev = report_data
        hist_block = ""
        if ev.get("has_historical_match"):
            hist_block = (
                f"MATCHED HISTORICAL ARCHIVE:\n"
                f"  Academic Year      : {ev.get('historical_academic_year', 'N/A')}\n"
                f"  Assignment         : {ev.get('historical_assignment', 'N/A')}\n"
                f"  Historical File    : {ev.get('hist_filename', 'N/A')}\n"
                f"  Historical Scope   : {ev.get('historical_total_lines', 0)} lines\n"
                f"  Matched Lines      : ~{ev.get('matched_lines_count', 0)} lines across "
                f"{ev.get('matched_blocks_count', 0)} block(s)\n"
            )
        else:
            hist_block = "MATCHED HISTORICAL ARCHIVE:\n  No comparable historical record found in repository.\n"

        # Build matched code evidence block
        evidence_block = ""
        sections = ev.get("matched_sections", [])
        if sections:
            evidence_block = "MATCHED CODE EVIDENCE BLOCKS:\n"
            for i, sec in enumerate(sections, 1):
                evidence_block += (
                    f"  [Block {i}] Student {sec['student_lines']} vs Historical {sec['historical_lines']}:\n"
                    f"    Student code snippet:\n"
                )
                for ln in sec["student_snippet"].splitlines():
                    evidence_block += f"      {ln}\n"
                if sec.get("historical_snippet"):
                    evidence_block += f"    Historical archive snippet:\n"
                    for ln in sec["historical_snippet"].splitlines():
                        evidence_block += f"      {ln}\n"
        else:
            evidence_block = "MATCHED CODE EVIDENCE BLOCKS: None recorded (structural/token similarity only).\n"

        # Prior Grok explanation as context
        prior_grok = ""
        if ev.get("grok_explanation"):
            prior_grok = (
                f"\nPRIOR GROK AI ANALYSIS (summary context, first 800 chars):\n"
                f"{ev['grok_explanation'][:800]}\n"
            )

        # Faculty review context
        review_block = (
            f"FACULTY REVIEW STATUS      : {ev.get('review_status', 'Pending Review')}\n"
            f"FACULTY REVIEW NOTES       : {ev.get('review_notes', 'None recorded')}\n"
        )

        user_prompt = (
            f"Generate a formal Academic Integrity Investigation Report using EXACTLY this 7-section structure:\n\n"
            f"## ACADEMIC INTEGRITY INVESTIGATION REPORT\n"
            f"### Case Reference: SUB-{ev['submission_id']} | Generated: {ev['generated_at']}\n\n"
            f"## Section 1 — Executive Summary\n"
            f"## Section 2 — Submission Profile & Context\n"
            f"## Section 3 — Algorithmic Detection Findings\n"
            f"## Section 4 — Code Evidence Analysis\n"
            f"## Section 5 — Comparative Structural Analysis\n"
            f"## Section 6 — Recommended Faculty Actions\n"
            f"## Section 7 — Formal Disclaimer\n\n"
            f"---\n\n"
            f"CASE DATA:\n\n"
            f"CASE REFERENCE             : SUB-{ev['submission_id']}\n"
            f"REPORT GENERATED           : {ev['generated_at']}\n"
            f"REVIEWED BY                : {ev['faculty_name']} ({ev['faculty_username']})\n"
            f"INSTITUTION SYSTEM         : CodeGuard Academic Portal\n\n"
            f"SUBMISSION DETAILS:\n"
            f"  Assignment               : {ev['assignment_title']}\n"
            f"  Subject                  : {ev['subject']}\n"
            f"  Programming Language     : {ev['language'].upper()}\n"
            f"  Submitted                : {ev['submitted_at']}\n"
            f"  Source File              : {ev['source_filename']}\n"
            f"  Analysis Status          : {ev['analysis_status']}\n"
            f"  Submission Scope         : {ev['student_total_lines']} lines\n\n"
            f"PLAGIARISM DETECTION METRICS:\n"
            f"  Text Similarity Score    : {ev['text_score']}%  (40% weight)\n"
            f"  AST Structural Score     : {ev['ast_score']}%  (60% weight)\n"
            f"  Combined Score           : {ev['combined_score']}%  [{ev['similarity_label']}]\n"
            f"  Algorithm Summary        : {ev['analysis_summary']}\n\n"
            f"{hist_block}\n"
            f"{evidence_block}\n"
            f"{review_block}"
            f"{prior_grok}\n"
            f"---\n\n"
            f"Section 7 MUST end with this verbatim disclaimer:\n"
            f"> This report is generated by CodeGuard's automated plagiarism detection system "
            f"and interpreted by xAI Grok AI. It constitutes decision-support evidence only. "
            f"Similarity scores are algorithmic indicators and do not constitute proof of academic "
            f"misconduct. The final determination of academic integrity violation rests solely "
            f"with the instructor and institutional academic integrity process. No student should "
            f"be disciplined based on this report alone without independent review."
        )

        return system_prompt, user_prompt

    @classmethod
    def generate_investigation_report(
        cls,
        submission_id: int,
        faculty_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates a formal long-form Academic Integrity Investigation Report using Grok.

        Pulls all submission, analysis, matched evidence, faculty review, and prior
        Grok explanation data, sends it to xAI Grok with a formal reporting prompt,
        and returns the generated markdown report text.
        """
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
                return {"success": False, "error": f"Submission #{submission_id} not found."}

            result = conn.execute("""
                SELECT r.id, r.text_similarity_score, r.ast_similarity_score,
                       r.combined_similarity_score, r.similarity_label, r.analysis_summary,
                       r.grok_explanation,
                       h.academic_year, h.assignment_name AS hist_assignment,
                       h.source_filename AS hist_filename, h.source_code AS hist_source_code
                FROM analysis_results r
                LEFT JOIN historical_submissions h ON r.matched_historical_id = h.id
                WHERE r.submission_id = ?
            """, (submission_id,)).fetchone()

            if not result:
                return {
                    "success": False,
                    "error": f"No analysis results found for submission #{submission_id}. "
                             "Run the plagiarism analysis first."
                }

            review = conn.execute("""
                SELECT f.review_status, f.review_notes
                FROM faculty_reviews f
                JOIN analysis_results r ON f.analysis_result_id = r.id
                WHERE r.submission_id = ?
            """, (submission_id,)).fetchone()

            evidence_rows = conn.execute("""
                SELECT details FROM matched_evidence WHERE analysis_result_id = ?
            """, (result["id"],)).fetchall()

        finally:
            conn.close()

        # Build matched sections (reuse extract_evidence_for_grok logic)
        evidence = cls.extract_evidence_for_grok(submission_id)
        matched_sections = evidence["matched_sections"] if evidence else []

        report_data = {
            "submission_id": submission_id,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "faculty_name": faculty_user.get("full_name", "Faculty Member"),
            "faculty_username": faculty_user.get("username", "N/A"),
            "assignment_title": sub["assignment_title"],
            "subject": sub["subject"],
            "language": sub["programming_language"],
            "submitted_at": sub["submitted_at"],
            "source_filename": sub["source_filename"],
            "analysis_status": sub["analysis_status"],
            "student_total_lines": len(sub["source_code"].splitlines()),
            "text_score": round(result["text_similarity_score"] or 0.0, 1),
            "ast_score": round(result["ast_similarity_score"] or 0.0, 1),
            "combined_score": round(result["combined_similarity_score"] or 0.0, 1),
            "similarity_label": result["similarity_label"] or "Low Similarity",
            "analysis_summary": result["analysis_summary"] or "",
            "grok_explanation": result["grok_explanation"] or "",
            "has_historical_match": bool(result["hist_filename"]),
            "historical_academic_year": result["academic_year"],
            "historical_assignment": result["hist_assignment"],
            "hist_filename": result["hist_filename"],
            "historical_total_lines": len((result["hist_source_code"] or "").splitlines()),
            "matched_lines_count": evidence["matched_lines_count"] if evidence else 0,
            "matched_blocks_count": evidence["matched_blocks_count"] if evidence else 0,
            "matched_sections": matched_sections,
            "review_status": review["review_status"] if review else "Pending Review",
            "review_notes": review["review_notes"] if review else "None recorded",
        }

        system_prompt, user_prompt = cls.build_report_prompts(report_data)

        # Use higher token limit for long-form report generation
        api_key = cls.get_api_key()
        if not api_key:
            return {
                "success": False,
                "error": "xAI API key is missing. Set the XAI_API_KEY environment variable to enable Investigation Report generation."
            }

        base_url = (os.environ.get("XAI_BASE_URL") or config.XAI_BASE_URL).rstrip("/")
        model = os.environ.get("XAI_MODEL") or config.XAI_MODEL or "grok-2-latest"
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.15,
            "max_tokens": 3000
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    report_text = choices[0]["message"].get("content", "").strip()
                    return {
                        "success": True,
                        "report": report_text,
                        "model": model,
                        "generated_at": report_data["generated_at"],
                        "submission_id": submission_id,
                        "faculty_name": report_data["faculty_name"],
                        "combined_score": report_data["combined_score"],
                        "similarity_label": report_data["similarity_label"],
                    }
                return {"success": False, "error": "Received an empty response from xAI Grok API."}
            elif response.status_code == 401:
                return {"success": False, "error": "xAI API authentication failed (401). Check your XAI_API_KEY."}
            elif response.status_code == 429:
                return {"success": False, "error": "xAI API rate limit exceeded (429). Try again shortly."}
            else:
                try:
                    err_msg = response.json().get("error", {}).get("message") or response.text
                except Exception:
                    err_msg = response.text
                return {"success": False, "error": f"xAI API error (HTTP {response.status_code}): {err_msg[:200]}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Connection to xAI Grok timed out (60s). Please try again."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Failed to connect to xAI Grok API. Check your network connection."}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

