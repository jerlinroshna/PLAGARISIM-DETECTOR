"""Vercel Serverless Function entry point for CodeGuard AST Plagiarism Detector."""
import sys
import os

# Ensure the project root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app

app = create_app()
