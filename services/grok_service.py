import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import requests
import config
import database
from services.grok_prompts import build_explanation_prompts, build_investigation_report_prompts
from services.grok_evidence import extract_submission_evidence, extract_report_evidence

logger = logging.getLogger(__name__)

class GrokService:
    """Service for interacting with the official xAI Grok API to provide evidence-grounded
    plagiarism analysis explanations and investigation reports for university faculty.
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
        """Extracts strictly necessary algorithmic evidence for Grok."""
        return extract_submission_evidence(submission_id)

    @classmethod
    def build_prompts(cls, evidence: Dict[str, Any]) -> Tuple[str, str]:
        """Constructs the system and user prompts for Grok submission explanation."""
        return build_explanation_prompts(evidence)

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
                    err_msg = response.json().get("error", {}).get("message") or response.text
                except Exception:
                    err_msg = response.text
                return {
                    "success": False,
                    "error": f"xAI API returned error status {response.status_code}: {err_msg[:200]}"
                }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Connection to the xAI Grok API timed out (30 seconds). Please check your internet connection or retry."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Could not establish a connection to the xAI Grok API. Please check your network or DNS settings."
            }
        except Exception as e:
            logger.exception("Unexpected error communicating with xAI API: %s", e)
            return {
                "success": False,
                "error": f"An unexpected error occurred while communicating with Grok: {str(e)}"
            }

    @classmethod
    def explain_submission(cls, submission_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Coordinates fetching evidence, calling Grok, and caching explanation in database."""
        api_key = cls.get_api_key()
        if not api_key:
            return {
                "success": False,
                "error": "xAI API key is missing. Set the XAI_API_KEY environment variable in your .env file or system environment to enable Grok AI explanations."
            }

        conn = database.get_db_connection()
        try:
            row = conn.execute("""
                SELECT id, grok_explanation, grok_explained_at
                FROM analysis_results
                WHERE submission_id = ?
            """, (submission_id,)).fetchone()

            if not row:
                return {
                    "success": False,
                    "error": f"Analysis result for submission ID {submission_id} not found.",
                    "error_type": "not_found"
                }

            analysis_result_id = row["id"]
            if row["grok_explanation"] and not force_refresh:
                return {
                    "success": True,
                    "explanation": row["grok_explanation"],
                    "cached": True,
                    "explained_at": row["grok_explained_at"]
                }
        finally:
            conn.close()

        evidence = cls.extract_evidence_for_grok(submission_id)
        if not evidence:
            return {
                "success": False,
                "error": f"Could not gather analysis evidence for submission ID {submission_id}.",
                "error_type": "no_evidence"
            }

        sys_prompt, usr_prompt = cls.build_prompts(evidence)
        result = cls.call_xai_api(sys_prompt, usr_prompt)

        if result.get("success") and result.get("explanation"):
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            conn = database.get_db_connection()
            try:
                conn.execute("""
                    UPDATE analysis_results
                    SET grok_explanation = ?, grok_explained_at = ?
                    WHERE id = ?
                """, (result["explanation"], now_str, analysis_result_id))
                conn.commit()
                result["cached"] = False
                result["explained_at"] = now_str
            finally:
                conn.close()

        return result

    @classmethod
    def build_report_prompts(cls, report_data: Dict[str, Any]) -> Tuple[str, str]:
        """Constructs system and user prompts for formal investigation report."""
        return build_investigation_report_prompts(report_data)

    @classmethod
    def generate_investigation_report(cls, submission_id: int, faculty_user: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a formal long-form Academic Integrity Investigation Report using Grok."""
        api_key = cls.get_api_key()
        if not api_key:
            return {
                "success": False,
                "error": "xAI API key is missing. Set the XAI_API_KEY environment variable to enable Investigation Report generation."
            }

        report_data = extract_report_evidence(submission_id, faculty_user)
        if not report_data:
            return {
                "success": False,
                "error": f"Could not gather report evidence for submission ID {submission_id}."
            }

        system_prompt, user_prompt = cls.build_report_prompts(report_data)

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
