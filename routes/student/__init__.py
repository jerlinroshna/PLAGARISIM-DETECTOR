from flask import Blueprint

student_bp = Blueprint("student", __name__, url_prefix="/student")

# Register all modular route handlers onto student_bp
from routes.student import dashboard
from routes.student import submit
from routes.student import submissions
from routes.student import historical
from routes.student import reports
from routes.student import notifications
from routes.student import profile

__all__ = ["student_bp"]
