# CareWise AI — Backend

FastAPI backend for the existing Google Stitch CareWise AI frontend.

## What is included

- Real `final_member_dataset.csv` (10,000 member records)
- Feature engineering from the original notebook
- Synthetic outreach-need target methodology from the original prototype
- Logistic Regression deployment model (selected by F1 in the supplied notebook workflow)
- Priority score 0–100 and priority bands
- SHAP member-level explanations
- Deterministic next-best-action rules
- Optional Gemini call-guide generation
- Fallback call guide when Gemini is unavailable
- Dashboard and analytics APIs
- Outreach status API
- CORS for frontend integration

## Important modeling note

The supplied dataset does not contain a historical outreach outcome. The notebook therefore creates a **synthetic outreach_need target** for prototype ML experimentation. The backend preserves that methodology. It should not be presented as a clinically validated or historically observed outcome.

The dataset contains 30-day utilization fields; the backend does not invent 12-month/quarterly time-series statistics.

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env  # macOS/Linux

uvicorn app.main:app --reload
```

API:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Gemini

Gemini is optional. Set `GEMINI_API_KEY` in `.env` when the team has the key. Without it, `/api/members/{member_id}/call-guide` returns the deterministic fallback guide.

Never commit the real key.

## Main endpoints

- `GET /api/dashboard`
- `GET /api/members`
- `GET /api/priority-queue`
- `GET /api/members/{member_id}`
- `GET /api/members/{member_id}/explanation`
- `GET /api/members/{member_id}/next-action`
- `POST /api/members/{member_id}/call-guide`
- `PATCH /api/members/{member_id}/outreach-status`
- `GET /api/analytics`
- `GET /api/model-performance`

## Stitch integration

Point the frontend API base URL to the FastAPI server, e.g. `http://127.0.0.1:8000`.

Replace prototype data in the Stitch HTML/React app with API calls. The backend is intentionally separate from the frontend so the existing Stitch design can remain unchanged.
