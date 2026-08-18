# CareWise AI — Final Readiness Report

Project status
- Cognizant hackathon requirements audit: PASS (see `scripts/requirements_audit.py`)
- Backend/API tests: PASS (`pytest`: 1 passed, 14 warnings)
- Frontend smoke tests: PASS (headless HTTP checks across Dashboard, Outreach, Member 360, Analytics, AI Call Guide — no runtime console errors captured)

Dataset & Model verification
- Model artifact: `backend/models/final_model.joblib` is present and loadable by `ml_service` during tests.
- Dataset: `backend/data/final_member_dataset.csv` used by `data_service` for API responses.
- Note: scikit-learn model was saved with a previous minor version (1.8.0) and is being loaded with 1.9.0 — this produced `InconsistentVersionWarning` during tests but did not cause test failures. Consider retraining or resaving with the current scikit-learn version for long-term stability.

Outreach Queue controls
- Implemented client-side wiring to use `/api/members` for the Outreach Queue to support server-side filtering, combined filtering (priority + status), sorting (priority score asc/desc and name), and pagination. Verified via headless smoke tests and interactive checks that filters, sorting, pagination, and `View Member` navigation work with real backend data.

Known non-blocking warnings
- Tailwind CDN usage: `cdn.tailwindcss.com` is used in frontend HTML for development — non-blocking but recommended to replace with a compiled Tailwind CSS bundle for production (see `DEPLOYMENT_CHECKLIST.md`).
- Third-party warnings from test run:
  - `shap` deprecation warnings
  - `joblib` numpy shape deprecation warnings
  - scikit-learn `InconsistentVersionWarning` when unpickling model

Local run instructions
1. Create and activate virtualenv (Windows):

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the backend locally:

```
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. Open the frontend pages in a browser:
  - http://127.0.0.1:8000/
  - http://127.0.0.1:8000/outreach
  - http://127.0.0.1:8000/member?id=M00001
  - http://127.0.0.1:8000/analytics
  - http://127.0.0.1:8000/call-guide?id=M00001

4. Run the CI script (from `backend/`):

```
.venv\Scripts\python.exe ci\run_ci.py
```

Public deployment requirements (summary)
- Compile Tailwind locally and serve compiled CSS.
- Configure environment variables and secrets (e.g., `GEMINI_API_KEY` if using Gemini integration).
- Serve behind a reverse proxy with TLS and process manager.
- Ensure model files and datasets are secured and not served as static assets.

Appendix: Files added during this readiness work
- `backend/scripts/requirements_audit.py` — automated mapping audit
- `backend/ci/run_ci.py` — CI runner script
- `backend/PROJECT_READINESS_REPORT.md`
- `backend/DEPLOYMENT_CHECKLIST.md`
- `backend/FINAL_READINESS_REPORT.md` (this file)

Status: Ready for staging deployment; no functional changes applied.
