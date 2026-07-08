# api/index.py — Vercel serverless entrypoint
# Vercel's @vercel/python builder looks for an `app` object in this file.
# We simply re-export the FastAPI app from the backend package.
import sys
import os

# Ensure the project root is on the path so `backend.*` imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app  # noqa: F401  — Vercel picks this up automatically
