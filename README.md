# 🏥 Care Management Outreach Prioritization Assistant

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.5+-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainable%20AI-FF6F00.svg)](https://shap.readthedocs.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Generative%20AI-8E75B2.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![SQLite / PostgreSQL](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

> **An Explainable, Action-Oriented AI Platform for Clinical Care-Management Teams to Predict 30-Day Outreach Need, Prioritize High-Risk Patients, Explain Risk Drivers via SHAP, and Deliver AI-Assisted Clinical Call Guidance.**

---

## 📑 Table of Contents

- [Executive Summary](#-executive-summary)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Machine Learning Pipeline & Benchmark](#-machine-learning-pipeline--benchmark)
- [Explainable AI (SHAP) & Next-Best Action](#-explainable-ai-shap--next-best-action)
- [Generative AI Call Guide](#-generative-ai-clinical-call-guide)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Quick Start](#-installation--quick-start)
- [API Endpoints & Swagger Docs](#-api-endpoints--swagger-docs)
- [UI Modules](#-ui-modules)
- [Automated Testing & CI](#-automated-testing--ci)
- [Academic & Presentation Artifacts](#-academic--presentation-artifacts)

---

## 🩺 Executive Summary

Healthcare care-management teams manage thousands of enrolled patients with complex chronic conditions, hospital discharges, unaddressed care gaps, and socioeconomic barriers. **Manual chart review is slow, inconsistent, and often causes delayed follow-ups**, leading to preventable Emergency Room (ER) visits and costly 30-day hospital readmissions.

**Care Management Outreach Prioritization Assistant** addresses this challenge through an end-to-end clinical triage pipeline:
1. **Predictive Risk Modeling:** Predicts member-level 30-day outreach need from electronic health records (EHR), claims, utilization, and Social Determinants of Health (SDOH).
2. **0–100 Priority Scoring:** Transforms calibrated model probabilities into intuitive continuous priority scores and stratifies members into **High**, **Medium**, and **Low** priority tiers.
3. **Transparent Explainability (XAI):** Deploys `shap.LinearExplainer` to extract individual positive risk drivers and maps them into clear clinical rationales.
4. **Deterministic Next-Best Actions:** Matches member acute conditions and open care gaps against evidence-based care coordination protocols.
5. **AI-Assisted Outreach Support:** Leverages Google Gemini to synthesize patient insights into personalized, empathetic conversational call guides for care managers.

---

## ✨ Key Features

- **🎯 Machine Learning Risk Stratification:** Benchmarked across 5 algorithms; powered by a calibrated **Logistic Regression Champion Pipeline** ($F_1 = 0.6457, \text{ROC-AUC} = 0.8674$).
- **📊 0–100 Dynamic Priority Queue:** Replaces rigid binary thresholds with continuous probability ranking so clinicians always contact the most vulnerable patients first.
- **🔍 Explainable AI (SHAP):** Game-theoretic local feature attributions isolate top risk drivers (e.g., recent emergency visits, discharge recency, medication gaps).
- **📋 Rule-Based Next-Best Action Engine:** Deterministic clinical hierarchy guarantees consistent, regulatory-compliant intervention recommendations.
- **🤖 GenAI Conversational Call Scripting:** Google Gemini API generates structured, non-diagnostic, member-centric call scripts with zero-failure local fallback templates.
- **⚡ High-Performance REST API:** Built with FastAPI, Pydantic validation, and SQLAlchemy ORM supporting both zero-configuration SQLite and production PostgreSQL.
- **🖥️ Responsive Care Manager Dashboard:** Features Priority Queue sorting, Member 360° Profile, Population Analytics, Care Gap Tracker, and Interactive Call Guides.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │                 DATA SOURCES (10,000 Lives)            │
                               │  Demographics • Chronic Diseases • 30-Day Utilization   │
                               │  Hospital Discharges • Care Gaps • SDOH Barriers       │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │           FEATURE ENGINEERING & PREPROCESSING           │
                               │  acute_utilization_30d • post_discharge_24h • SDOH Sum │
                               │  Discharge -1 Imputation • StandardScaler (Pipeline)   │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │            MACHINE LEARNING INFERENCE ENGINE           │
                               │  Champion: Logistic Regression (F1: 0.6457 | AUC: 0.8674)│
                               │  Outputs Calibrated Probability P(outreach_need = 1)   │
                               └─────────────┬────────────────────────────┬─────────────┘
                                             │                            │
                                             ▼                            ▼
                      ┌──────────────────────────────┐     ┌──────────────────────────────┐
                      │    0–100 PRIORITY SCORING    │     │   SHAP EXPLAINABILITY (XAI)  │
                      │  High Priority (>70)         │     │  shap.LinearExplainer        │
                      │  Medium Priority (41–70)     │     │  Top-3 Positive Risk Drivers │
                      │  Low Priority (≤40)          │     │  Human-Readable Reason Map   │
                      └──────────────┬───────────────┘     └──────────────┬───────────────┘
                                     │                                    │
                                     └──────────────────┬─────────────────┘
                                                        │
                                                        ▼
                               ┌────────────────────────────────────────────────────────┐
                               │          ACTION ENGINE & GENERATIVE AI GUIDANCE        │
                               │  Deterministic Next-Best Action (Clinical Rules)       │
                               │  Google Gemini API (Personalized Call Scripting)       │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │               CARE MANAGEMENT APPLICATION              │
                               │  FastAPI REST API • SQLAlchemy • SQLite / PostgreSQL   │
                               │  Dashboard • Priority Queue • Member 360 • Analytics   │
                               └────────────────────────────────────────────────────────┘
```

---

## 🤖 Machine Learning Pipeline & Benchmark

### 1. Cohort & Feature Matrix
- **Cohort Size:** 10,000 patient records (Synthetic, HIPAA-safe).
- **Features ($X$):** 22 total predictors (Demographics, Conditions, Acute Utilization, Care Gaps, SDOH).
- **Target ($y$):** `outreach_need` (2,500 Positive Cases [25.0%] / 7,500 Negative Cases [75.0%]).
- **Split Strategy:** Stratified 80:20 Split (8,000 Train / 2,000 Test) with `random_state=42`.
- **Preprocessing:** `StandardScaler` fitted strictly on `X_train` within a Scikit-Learn `Pipeline` to eliminate data leakage.

### 2. Candidate Model Benchmark (Test Set: 2,000 Records)

| Model Architecture | Accuracy | Precision | Recall | F1-Score | PR-AUC | ROC-AUC | Confusion Matrix `[TN, FP / FN, TP]` | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Logistic Regression** | **0.8480** | **0.7737** | **0.5540** | **0.6457** | **0.7531** | **0.8674** | `[1419, 81 / 223, 277]` | 🏆 **Champion** |
| **XGBoost Classifier** | 0.8385 | 0.7335 | 0.5560 | 0.6325 | 0.7375 | 0.8603 | `[1399, 101 / 222, 278]` | Benchmark |
| **CatBoost Classifier** | 0.8395 | 0.7493 | 0.5380 | 0.6263 | 0.7360 | 0.8604 | `[1410, 90 / 231, 269]` | Benchmark |
| **Support Vector Machine (SVM)**| 0.8420 | 0.7857 | 0.5060 | 0.6156 | 0.7089 | 0.8064 | `[1431, 69 / 247, 253]` | Benchmark |
| **Random Forest Classifier** | 0.7945 | 0.5941 | 0.5620 | 0.5776 | 0.6146 | 0.8134 | `[1308, 192 / 219, 281]` | Benchmark |

### 3. Why Logistic Regression Was Selected
- **Top Performance:** Highest F1-Score (0.6457), ROC-AUC (0.8674), and PR-AUC (0.7531).
- **Additive Clinical Fit:** Chronic multi-morbidity risk accumulates linearly; regularized Logistic Regression generalized best without overfitting localized noise.
- **Calibrated Probabilities:** Direct posterior probabilities yield smooth 0–100 priority scores.
- **Instant Explainability:** Compatible with `shap.LinearExplainer` for exact, game-theoretic attributions.

---

## 🔍 Explainable AI (SHAP) & Next-Best Action

### Explainable AI (SHAP)
Traditional ML outputs a raw score without clinical context. We apply **SHAP LinearExplainer** to isolate the top-3 positive risk drivers for each individual member:

$$\phi_i = w_i \cdot (x_i - \mu_i)$$

* **Raw Feature:** `er_visits_30d` $\longrightarrow$ **UI Explanation:** *"Recent emergency-room visits increased priority"*
* **Raw Feature:** `medication_gap` $\longrightarrow$ **UI Explanation:** *"Medication gap increased priority"*
* **Raw Feature:** `recent_discharge_30d` $\longrightarrow$ **UI Explanation:** *"Recent hospital discharge increased priority"*

### Deterministic Next-Best Action Engine
To guarantee clinical safety and protocol adherence, recommendations follow a deterministic rule hierarchy:
1. **`post_discharge_24h == 1`:** *"Complete timely outreach and confirm follow-up needs after the recent care event signal."*
2. **`recent_discharge_30d == 1`:** *"Conduct follow-up for the recent care event signal and review care-coordination needs."*
3. **`medication_gap == 1`:** *"Address the identified medication-related care gap with the care team."*
4. **`overdue_screening == 1` or `overdue_lab == 1`:** *"Review overdue screening or lab care gaps and coordinate follow-up."*
5. **`transportation_barrier == 1`:** *"Assess transportation needs that may affect access to follow-up care."*
6. **`food_insecurity / housing / financial == 1`:** *"Assess identified social-support needs and coordinate appropriate resources."*

---

## 🗣️ Generative AI Clinical Call Guide

Integrated with **Google Gemini API** (`gemini-1.5-flash` / `gemini-2.5-flash`), the system transforms structured patient records into a personalized dialogue guide for clinical staff:
- **Input Context:** Member name, age, chronic conditions, Priority Score, top-3 SHAP drivers, care gaps, and Next-Best Action.
- **Safety Prompting:** Strict non-diagnostic persona instructions prevent hallucinated diagnoses or medical dosage advice.
- **Fallback Architecture:** A deterministic local script generator ensures nurses always have call guidance even if the network or API is offline.

---

## 📁 Project Directory Structure

```
Care-management-outreach-prioritization-assistant/
│
├── START_ASSISTANT.bat                  # 1-Click Startup Script for Windows
├── README.md                            # Comprehensive Project Documentation
├── Care_Management_ML_Complete_Notes.pdf # Complete ML Study & Viva Guide (PDF)
├── Care_Management_ML_Cheatsheet.pdf    # High-Yield Revision Cheatsheet (PDF)
├── PPT_project (2).pptx                 # Project Presentation Deck (27 Slides)
│
├── backend/                             # Core FastAPI Backend Application
│   ├── requirements.txt                 # Python Dependencies
│   ├── .env.example                     # Environment Configuration Template
│   │
│   ├── app/                             # Application Module
│   │   ├── main.py                      # FastAPI App, Routes, Static Mounting
│   │   ├── db/                          # Database & ORM Layer
│   │   │   ├── session.py               # Engine & Session Management
│   │   │   ├── models.py                # Member, OutreachStatus, Campaign ORM Models
│   │   │   └── init_db.py               # Database Auto-Seeding & Init
│   │   ├── schemas/                     # Data Validation & Pydantic Models
│   │   │   └── api_models.py            # API Request & Response Schemas
│   │   └── services/                    # Business & ML Logic
│   │       ├── data_service.py          # Member Query & Filtering Logic
│   │       ├── ml_service.py            # Model Scoring & SHAP Explainer
│   │       ├── action_service.py        # Rule-Based Next-Best Action Logic
│   │       ├── gemini_service.py        # Gemini Call Script Generation & Fallback
│   │       └── auth_service.py          # Authentication & Security
│   │
│   ├── data/                            # Data Files
│   │   ├── carewise.db                  # SQLite Application Database
│   │   ├── final_member_dataset.csv     # 10K Processed Member Dataset
│   │   └── outreach_status.json         # Outreach Workflow State
│   │
│   ├── frontend/                        # Web Dashboard & UI Pages
│   │   ├── index.html                   # Executive Dashboard
│   │   ├── outreach.html                # Outreach Priority Queue
│   │   ├── member.html                  # Member 360° Profile
│   │   ├── analytics.html               # Population & Model Analytics
│   │   ├── call-guide.html              # AI Clinical Call Guide
│   │   ├── care-gaps.html               # Care Gap Campaigns
│   │   ├── sidebar.js                   # Common Navigation Component
│   │   └── brand-mark.svg               # Application Logo
│   │
│   ├── models/                          # Trained ML & SHAP Artifacts
│   │   ├── final_model.joblib           # Trained Logistic Regression Pipeline
│   │   ├── metadata.json                # Model Metadata & Features List
│   │   ├── model_metrics.csv            # 5-Model Benchmark Comparison Table
│   │   └── shap_values.npy              # Precomputed 10K SHAP Values
│   │
│   ├── scripts/                         # Maintenance & Verification Scripts
│   │   ├── init_db.py                   # DB Re-initialization CLI
│   │   └── requirements_audit.py        # Requirements Verification Script
│   │
│   ├── tests/                           # Pytest Test Suite
│   │   └── test_api.py                  # API Endpoint & ML Verification Tests
│   │
│   └── ci/                              # Continuous Integration
│       └── run_ci.py                    # Automated CI Test Runner
│
└── unwanted/                            # Reference Materials & Jupyter Notebook
    └── Care_Management_Outreach_Prioritization_Assistant_final.ipynb
```

---

## 🚀 Installation & Quick Start

### Prerequisites
- **Python 3.11+** installed ([python.org](https://www.python.org/))
- **Git** installed

### Method 1: 1-Click Startup (Windows)
Double-click `START_ASSISTANT.bat` in the root folder. The script automatically sets up the virtual environment, installs dependencies, initializes the database, and launches the server.

### Method 2: Manual Terminal Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mrvrpatils/Care-management-outreach-prioritization-assistant.git
   cd Care-management-outreach-prioritization-assistant
   ```

2. **Navigate to the backend and create a virtual environment:**
   ```bash
   cd backend
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables (Optional):**
   Copy `.env.example` to `.env`:
   ```env
   # Database: Defaults to SQLite if omitted
   DATABASE_URL=sqlite:///./data/carewise.db

   # Optional: Google Gemini API Key for dynamic GenAI call guides
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

6. **Initialize the Database:**
   ```bash
   python scripts/init_db.py
   ```

7. **Start the FastAPI Application:**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

8. **Access the Application:**
   - **Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🌐 API Endpoints & Swagger Docs

The FastAPI backend exposes fully documented REST endpoints accessible at `/docs`:

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/health` | Application, database, and model health check. |
| `GET` | `/api/dashboard/stats` | Executive KPI cards (Total Members, High Priority, Open Gaps, Discharges). |
| `GET` | `/api/members/queue` | Paginated, filterable outreach priority queue sorted by Priority Score. |
| `GET` | `/api/members/{member_id}` | Member 360° profile with clinical, SDOH, SHAP, and Next-Best Action details. |
| `POST` | `/api/members/{member_id}/status` | Updates outreach status (Pending, Contacted, Scheduled, Completed). |
| `GET` | `/api/analytics/model` | Model benchmark comparison metrics, ROC-AUC, PR-AUC, and feature rankings. |
| `GET` | `/api/analytics/population`| Cohort risk distributions, SDOH breakdowns, and clinical burden stats. |
| `POST` | `/api/call-guide/{member_id}` | Triggers Gemini API to generate personalized conversational call guidance. |
| `GET` | `/api/care-gaps/summary` | Care gap metrics across preventive screenings, labs, and medications. |

---

## 🖥️ UI Modules

| Module | Route | Key Capabilities |
| :--- | :--- | :--- |
| **Executive Dashboard** | `/` | Real-time population KPIs, high-risk alerts, and 30-day outreach progress. |
| **Outreach Priority Queue** | `/outreach` | Dynamic priority ranking, High/Medium/Low filtering, search by condition/ID. |
| **Member 360° View** | `/member?id=M00001` | Clinical history, SDOH barrier badges, SHAP risk drivers, and care plan. |
| **Population Analytics** | `/analytics` | Interactive charts for model evaluation, confusion matrix, and feature importance. |
| **AI Clinical Call Guide** | `/call-guide?id=M00001`| AI-generated patient call scripts, outreach objectives, and call logging. |
| **Care Gap Campaigns** | `/care-gaps` | Targeted cohorts for overdue screenings, HbA1c/lipid labs, and medication gaps. |

---

## 🧪 Automated Testing & CI

Execute the automated test suite to verify database queries, ML scoring pipelines, SHAP outputs, and API routes:

```powershell
cd backend
pytest tests/ -v
```

Run the complete Continuous Integration (CI) verification script:
```powershell
python ci/run_ci.py
```

---

## 📚 Academic & Presentation Artifacts

The repository includes study notes and viva reference documents based on the project implementation:
- 📖 **Complete Machine Learning Notes (PDF):** `Care_Management_ML_Complete_Notes.pdf` (20-section detailed guide covering formulas, math, SHAP explanations, code breakdowns, and 30 viva questions)
- ⚡ **High-Yield ML Cheatsheet (PDF):** `Care_Management_ML_Cheatsheet.pdf` (Fast-revision sheet summarizing the pipeline, metrics table, and top 10 viva answers)
- 📊 **Project Presentation Deck (PPTX):** `PPT_project (2).pptx` (Official 27-slide presentation covering problem statement, architecture, ML benchmark, and results)

---

## 👥 Project Team & Credits

- **Project:** Care Management Outreach Prioritization Assistant
- **Team:** Team 51
- **Domain:** Healthcare Artificial Intelligence / Clinical Decision Support Systems
- **Repository:** [GitHub Repository](https://github.com/mrvrpatils/Care-management-outreach-prioritization-assistant)
