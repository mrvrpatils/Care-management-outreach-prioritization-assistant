import sys
from pathlib import Path

# Ensure backend and root directories are in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

for p in (BACKEND_DIR, ROOT_DIR, Path("/var/task"), Path("/var/task/backend")):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.main import app

# Explicit top-level exports for Vercel Serverless Function runtime
application = app
handler = app
