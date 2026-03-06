"""
run.py — Project entry point.

Usage:
    python run.py            # development server
    uvicorn app.main:app --reload  # alternative (same thing)
"""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Startup diagnostics
db_password = os.getenv("DB_PASSWORD", "")
db_user = os.getenv("DB_USER", "NOT SET")
db_host = os.getenv("DB_HOST", "NOT SET")
db_port = os.getenv("DB_PORT", "NOT SET")
db_name = os.getenv("DB_NAME", "NOT SET")

if not db_password:
    print("⚠  WARNING: DB_PASSWORD not found in environment variables!")
    print(f"   DB_HOST : {db_host}")
    print(f"   DB_NAME : {db_name}")
    print(f"   DB_USER : {db_user}")
    print(f"   DB_PORT : {db_port}")
else:
    print(f"✓  Database config loaded: {db_user}@{db_host}:{db_port}/{db_name}")

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    print(f"✓  Starting server on http://0.0.0.0:{port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,          # auto-reload on file changes during development
        reload_dirs=["app"],  # only watch the app/ directory
    )
