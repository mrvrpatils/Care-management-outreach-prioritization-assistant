# Care Management Outreach Prioritization Assistant — Complete Project

Care Management Outreach Prioritization Assistant is an AI-powered clinical outreach prioritization platform built with **FastAPI**, **SQLAlchemy**, **Scikit-Learn / SHAP**, and a responsive modern frontend interface.

---

## 📁 Project Structure

```
Care-management-outreach-prioritization-assistant/
├── START_ASSISTANT.bat         # 1-click startup script (Windows)
├── README.md                   # Project overview and instructions
├── docs/                       # Project documentation and specifications
│   ├── DATA_ANALYSIS_NOTES.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── FINAL_READINESS_REPORT.md
│   ├── FRONTEND_API_MAPPING.md
│   └── PROJECT_READINESS_REPORT.md
└── backend/                    # Core application directory
    ├── requirements.txt        # Python dependencies
    ├── .env.example            # Environment configuration template
    ├── app/                    # FastAPI application module
    │   ├── main.py             # FastAPI entry point & API endpoints
    │   ├── db/                 # Database layer (SQLAlchemy)
    │   │   ├── session.py      # Engine, SessionLocal, Base, DATABASE_URL config
    │   │   ├── models.py       # MemberModel, OutreachStatusModel, CampaignModel
    │   │   └── init_db.py      # Database table initialization & auto-seeding
    │   ├── schemas/            # Pydantic request/response models
    │   │   └── api_models.py
    │   └── services/           # Business logic & ML scoring
    │       ├── data_service.py # Database & data service layer
    │       ├── ml_service.py   # Model prediction & SHAP explanations
    │       ├── action_service.py # Next best action engine
    │       └── gemini_service.py # AI Call Guide generator & fallback
    ├── data/                   # Data storage
    │   ├── carewise.db         # SQLite database (auto-created & seeded)
    │   ├── final_member_dataset.csv
    │   └── outreach_status.json
    ├── frontend/               # UI HTML, JavaScript, and asset files
    │   ├── index.html          # Dashboard
    │   ├── outreach.html       # Outreach Priority Queue
    │   ├── member.html         # Member 360 View
    │   ├── analytics.html      # Population Analytics
    │   ├── call-guide.html     # AI Clinical Call Guide
    │   ├── care-gaps.html      # Care Gap Interventions
    │   ├── sidebar.js          # Navigation logic
    │   └── brand-mark.svg      # Logo
    ├── models/                 # Pretrained ML & SHAP artifacts
    │   ├── final_model.joblib
    │   ├── metadata.json
    │   ├── model_metrics.csv
    │   └── shap_values.npy
    ├── scripts/                # Utility scripts
    │   ├── init_db.py          # Database initialization CLI
    │   └── requirements_audit.py # API audit script
    ├── tests/                  # Automated pytest test suite
    │   └── test_api.py
    └── ci/                     # Continuous integration test runner
        └── run_ci.py
```

---

## 🚀 Quick Start

### Option 1: Double-click Startup (Windows)
Double click `START_ASSISTANT.bat` in the project root.

### Option 2: Terminal / VS Code
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 🗄️ Database Configuration

By default, the assistant uses **SQLite** (`backend/data/carewise.db`) with zero setup needed.

To use **PostgreSQL** or **MySQL**, create a `backend/.env` file:
```env
# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/care_management

# MySQL
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/care_management

# Optional Gemini API Key for dynamic LLM call guide generation
GEMINI_API_KEY=your_key_here
```

To reinitialize or re-seed database tables at any time:
```powershell
cd backend
python scripts/init_db.py
```

---

## 🧪 Testing

Run the automated test suite:
```powershell
cd backend
pytest tests/ -v
```

---

## 🌐 Application Routes

| Route | Description |
|---|---|
| `/` | Dashboard |
| `/outreach` | Outreach Priority Queue |
| `/member?id=M00001` | Member 360 Profile |
| `/analytics` | Population & Model Analytics |
| `/call-guide?id=M00001` | AI Clinical Call Guide |
| `/care-gaps` | Care Gap Campaigns |
| `/health` | API & Database Health Check |
| `/docs` | Interactive Swagger API Documentation |
