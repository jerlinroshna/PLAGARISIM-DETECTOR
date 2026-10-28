#!/usr/bin/env python3
"""
Application Runner for CodeGuard AST Plagiarism Detector.
Usage:
    python run.py
"""
import os
import config
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    print("=" * 65)
    print("   CodeGuard AST: Source Code Plagiarism Detector Portal")
    print(f"   Server listening at: http://127.0.0.1:{port}")
    print("   Mode: " + ("Development (Debug On)" if debug else "Production"))
    print("=" * 65)
    app.run(host="127.0.0.1", port=port, debug=debug)
