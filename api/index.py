import sys
from pathlib import Path

# Ensure backend and root directories are in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

for p in (BACKEND_DIR, ROOT_DIR, Path("/var/task"), Path("/var/task/backend")):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from app.main import app
except Exception as e:
    import traceback
    err_msg = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    
    app = FastAPI(title="Care Management Assistant")
    
    @app.get("/{rest_of_path:path}")
    def fallback_handler(rest_of_path: str):
        return HTMLResponse(
            status_code=500,
            content=f"<h3>Server Initialization Error</h3><pre>{err_msg}</pre>"
        )
