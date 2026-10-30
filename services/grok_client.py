import os
import logging
from typing import Dict, Any
import requests
import config

logger = logging.getLogger(__name__)

def execute_xai_chat(system_prompt: str, user_prompt: str, api_key: str, max_tokens: int = 1500, temperature: float = 0.2) -> Dict[str, Any]:
    """Executes a chat completion call to the xAI Grok API endpoint."""
    if not api_key:
        return {
            "success": False,
            "error": "xAI API key is missing. Please set XAI_API_KEY environment variable or in config.",
            "error_type": "missing_api_key"
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": config.XAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(
            config.XAI_API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=config.XAI_TIMEOUT_SECONDS
        )

        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "").strip()
                return {
                    "success": True,
                    "explanation": content,
                    "model": data.get("model", config.XAI_MODEL),
                    "usage": data.get("usage", {})
                }
            return {
                "success": False,
                "error": "Invalid response format from xAI API (no choices returned).",
                "error_type": "empty_response"
            }

        elif response.status_code in (401, 403):
            return {
                "success": False,
                "error": "Authentication failed with xAI API. Please check your XAI_API_KEY.",
                "error_type": "auth_error",
                "status_code": response.status_code
            }
        elif response.status_code == 429:
            return {
                "success": False,
                "error": "Rate limit exceeded for xAI API. Please try again shortly.",
                "error_type": "rate_limit",
                "status_code": 429
            }
        else:
            return {
                "success": False,
                "error": f"xAI API returned error status {response.status_code}: {response.text[:200]}",
                "error_type": "api_error",
                "status_code": response.status_code
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": f"Request to xAI Grok API timed out after {config.XAI_TIMEOUT_SECONDS}s.",
            "error_type": "timeout"
        }
    except requests.exceptions.RequestException as e:
        logger.exception("Network error while connecting to xAI API: %s", e)
        return {
            "success": False,
            "error": f"Network error connecting to xAI Grok: {str(e)}",
            "error_type": "network_error"
        }
    except Exception as e:
        logger.exception("Unexpected error calling xAI API: %s", e)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "internal_error"
        }

