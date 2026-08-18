# Deployment Checklist — Care Management Outreach Prioritization Assistant (backend)

1) Environment & dependencies
   - Create a Python 3.11+ virtual environment and install requirements:

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     pip install -r requirements.txt
     ```

   - Verify `backend/models/final_model.joblib` and related artifacts exist and are accessible by the running process.

2) Frontend build (recommended)
   - Replace CDN Tailwind in production by installing Tailwind locally and compiling a minimized CSS bundle.
   - Build steps (example):

     ```powershell
     npm init -y
     npm install -D tailwindcss postcss autoprefixer
     npx tailwindcss -i ./frontend/input.css -o ./frontend/dist/output.css --minify
     ```

   - Update the HTML pages to reference the compiled `./frontend/dist/output.css` instead of CDN in production.

3) Configuration / Secrets
   - Create an environment file or environment variables for production:
     - `ENV=production`
     - `GEMINI_API_KEY` (optional)
     - Any other service credentials

4) Run server (recommended production stack)
   - Use Uvicorn with multiple workers or Gunicorn + Uvicorn workers behind Nginx.

     Example with Uvicorn:
     ```powershell
     .\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
     ```

     Example with Gunicorn on Linux:
     ```bash
     gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4 -b 0.0.0.0:8000
     ```

5) Reverse proxy & TLS
   - Configure Nginx to proxy HTTP -> Uvicorn/Gunicorn and enable HTTPS (Let's Encrypt or other CA).

6) Process management
   - Use `systemd` (Linux) or a Windows service/Task Scheduler for auto-start and restarts.

7) Logging & Monitoring
   - Configure structured logging for the app; forward logs to a centralized store.
   - Add application performance monitoring (Sentry, Datadog) for runtime errors.

8) Security
   - Ensure model artifacts and dataset files are not publicly accessible via web server paths.
   - Use HTTPS, strong secrets management, and least-privilege file permissions.

9) Scale & storage
   - If serving many concurrent requests or large models, place model files on fast local disk and tune worker counts.

10) Smoke test after deployment
   - Verify main routes: `/`, `/outreach`, `/member?id=<sample>`, `/analytics`, `/call-guide?id=<sample>`
   - Confirm logs show no runtime JS errors and API endpoints return expected JSON.
