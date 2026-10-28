import os
from flask import Flask, render_template, session
import config
import database
from auth import get_current_user
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.faculty_routes import faculty_bp

def create_app():
    """Application factory for the Plagiarism Detector portal."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    # Initialize database tables and seed accounts
    database.init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)

    @app.context_processor
    def inject_user():
        user = get_current_user()
        unread_notifications_count = 0
        user_notifications = []
        if user and user.get("role") == "student":
            try:
                conn = database.get_db_connection()
                row = conn.execute(
                    "SELECT COUNT(*) FROM student_notifications WHERE student_id = ? AND is_read = 0",
                    (user["id"],)
                ).fetchone()
                if row:
                    unread_notifications_count = row[0]
                user_notifications = conn.execute(
                    "SELECT * FROM student_notifications WHERE student_id = ? ORDER BY created_at DESC LIMIT 5",
                    (user["id"],)
                ).fetchall()
                conn.close()
            except Exception:
                pass
        return {
            "current_user": user,
            "config": config,
            "unread_notifications_count": unread_notifications_count,
            "user_notifications": user_notifications
        }

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("base.html", error_title="403 Access Forbidden",
                               error_msg="You do not have permission to access this resource."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("base.html", error_title="404 Page Not Found",
                               error_msg="The requested page could not be located."), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template("base.html", error_title="413 File Too Large",
                               error_msg="The uploaded file exceeds the 5 MB file size limit."), 413

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("base.html", error_title="500 Internal Error",
                               error_msg="An unexpected error occurred while processing the request."), 500

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting SIH Plagiarism Detector Portal on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
