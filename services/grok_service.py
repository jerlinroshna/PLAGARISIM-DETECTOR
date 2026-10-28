import os
import json
import logging
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
