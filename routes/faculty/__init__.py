from flask import Blueprint

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

# Register all modular route handlers onto faculty_bp
from routes.faculty import dashboard
from routes.faculty import assignments
from routes.faculty import submissions
from routes.faculty import historical
from routes.faculty import investigation
from routes.faculty import reports

__all__ = ["faculty_bp"]
