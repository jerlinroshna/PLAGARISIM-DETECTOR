import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env file if available
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        try:
            with open(_env_path, "r", encoding="utf-8") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line and not _line.startswith("#") and "=" in _line:
                        _k, _v = _line.split("=", 1)
                        _k = _k.strip()
                        _v = _v.strip().strip("'\"")
                        if _k not in os.environ:
                            os.environ[_k] = _v
        except Exception:
            pass

SECRET_KEY = os.environ.get("SECRET_KEY", "sih-plagiarism-detector-secret-key-2026-secure")

# xAI Grok API Configuration
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_BASE_URL = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_MODEL = os.environ.get("XAI_MODEL", "grok-2-latest")

# Serverless / Vercel environment detection
IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    DATA_DIR = "/tmp/data"
    UPLOADS_DIR = "/tmp/uploads"
else:
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

DATABASE_PATH = os.path.join(DATA_DIR, "plagiarism_detector.db")
DEMO_ACCOUNTS_CSV = os.path.join(BASE_DIR, "data", "demo_accounts.csv")

UPLOADS_SUBMISSIONS_DIR = os.path.join(UPLOADS_DIR, "submissions")
UPLOADS_HISTORICAL_DIR = os.path.join(UPLOADS_DIR, "historical")

# Maximum upload file size (5 MB)
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

# Supported source file extensions mapped to canonical language names
ALLOWED_EXTENSIONS = {
    "py": "python",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "js": "javascript"
}

LANGUAGE_DISPLAY_NAMES = {
    "python": "Python (.py)",
    "java": "Java (.java)",
    "c": "C (.c)",
    "cpp": "C++ (.cpp)",
    "javascript": "JavaScript (.js)"
}

# Similarity scoring weights & classification thresholds
WEIGHT_TEXT = 0.40
WEIGHT_AST = 0.60

THRESHOLD_HIGH = 70.0
THRESHOLD_MEDIUM = 30.0
