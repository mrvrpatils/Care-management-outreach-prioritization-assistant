
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Response, Depends, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
for env_path in (BACKEND_DIR / ".env", ROOT_DIR / ".env", BACKEND_DIR / "ci" / ".env"):
    if env_path.is_file():
        load_dotenv(env_path)
        break

from .services.data_service import data_service, population_statistics, utilization_statistics
from .services.ml_service import ml_service
from .services.action_service import next_best_action
from .services.gemini_service import fallback_call_guide, generate_call_guide, generate_dashboard_insight
from .services.auth_service import (
    register_user, authenticate_user, create_access_token, verify_access_token, get_user_by_id
)
from .schemas.api_models import (
    OutreachStatusUpdate, CallGuideRequest, UserRegisterRequest, UserLoginRequest, UserResponse, AuthTokenResponse
)
from .db import init_db, SessionLocal, get_db, CampaignModel, MemberModel, OutreachStatusModel, LoginModel

# In-memory prediction cache built from the real dataset/artifacts.
predictions = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global predictions
    init_db()
    probs, scores, bands = ml_service.initialize(data_service.df)
    data_service.df["outreach_probability"] = probs
    data_service.df["priority_score"] = scores
    data_service.df["priority_band"] = bands
    data_service.df["next_best_action"] = data_service.df.apply(next_best_action, axis=1)
    predictions = True
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Care Management Outreach Prioritization Assistant Backend",
    version="1.0.0",
    description="FastAPI backend for the Care Management Outreach Prioritization Assistant."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend from this same FastAPI application.
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend" if (ROOT_DIR / "frontend").is_dir() else BACKEND_DIR / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(FRONTEND_DIR / "login.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/outreach", include_in_schema=False)
def outreach_page():
    return FileResponse(FRONTEND_DIR / "outreach.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/member", include_in_schema=False)
def member_page():
    return FileResponse(FRONTEND_DIR / "member.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/analytics", include_in_schema=False)
def analytics_page():
    return FileResponse(FRONTEND_DIR / "analytics.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/call-guide", include_in_schema=False)
def call_guide_page():
    return FileResponse(FRONTEND_DIR / "call-guide.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/care-gaps", include_in_schema=False)
def care_gaps_page():
    return FileResponse(FRONTEND_DIR / "care-gaps.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


# Authentication Endpoints
@app.post("/api/auth/register", response_model=AuthTokenResponse)
def api_register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload)
        token = create_access_token(user.id, user.username, user.role, user.full_name)
        user_res = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            created_at=user.created_at.isoformat() if user.created_at else None,
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        return AuthTokenResponse(access_token=token, user=user_res)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/auth/login", response_model=AuthTokenResponse)
def api_login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = create_access_token(user.id, user.username, user.role, user.full_name)
    user_res = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )
    return AuthTokenResponse(access_token=token, user=user_res)


@app.get("/api/auth/me", response_model=UserResponse)
def api_me(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split(" ", 1)[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token expired or invalid.")
    user_id = int(payload["sub"])
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@app.post("/api/auth/logout")
def api_logout():
    return {"status": "ok", "message": "Successfully logged out."}



# Minimal in-memory campaign store for UI workflows
campaign_store = {}

@app.get('/api/care-gaps/{field}/summary')
def care_gaps_summary(field: str):
    # field is expected to be one of the columns used for overdue flags
    df = data_service.df
    if field not in df.columns:
        raise HTTPException(status_code=404, detail='Unknown care-gap field')
    count_members = int((df[field] > 0).sum())
    open_gaps = int((df[field] > 0).sum())
    return {'field': field, 'count': count_members, 'open_gaps': open_gaps}

@app.post('/api/care-gaps/{field}/campaign')
def create_care_gap_campaign(field: str, initiator: Optional[str] = None):
    df = data_service.df
    if field not in df.columns:
        raise HTTPException(status_code=404, detail='Unknown care-gap field')
    members = df[df[field] > 0]['member_id'].astype(str).tolist()
    campaign_id = f"camp_{len(campaign_store)+1}"
    sample_members = members[:20]
    campaign_store[campaign_id] = {
        'field': field,
        'initiator': initiator,
        'member_count': len(members),
        'members_sample': sample_members
    }
    # Persist to database
    db = SessionLocal()
    try:
        import json
        camp_record = CampaignModel(
            campaign_id=campaign_id,
            field=field,
            initiator=initiator,
            member_count=len(members),
            members_sample_json=json.dumps(sample_members),
        )
        db.add(camp_record)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return {'campaign_id': campaign_id, 'member_count': len(members)}

def row_to_member(row):
    return {
        "member_id": str(row["member_id"]),
        "member_name": str(row["member_name"]),
        "priority_score": round(float(row["priority_score"]), 2),
        "priority_band": str(row["priority_band"]),
        "outreach_probability": round(float(row["outreach_probability"]), 4),
        "main_risk_factors": get_risk_factors(row),
        "next_best_action": str(row["next_best_action"]),
        "outreach_status": data_service.get_status(row["member_id"]),
    }

def get_risk_factors(row):
    factors = []
    # This dataset contains a discharge *signal*, not a dated event record.
    # Keep outward-facing labels faithful to that distinction.
    if int(row["recent_discharge_30d"]) == 1: factors.append("Recent care event signal")
    if int(row["er_visits_30d"]) > 0: factors.append("Recent ER utilization")
    if int(row["hospitalizations_30d"]) > 0: factors.append("Recent hospitalization")
    if int(row["care_gap_count"]) > 0: factors.append("Open care gaps")
    if int(row["medication_gap"]) == 1: factors.append("Medication gap")
    if int(row["social_risk_count"]) > 0: factors.append("Social-risk factors")
    if not factors: factors.append("Model-identified outreach factors")
    return factors[:3]

@app.get("/health")
def health():
    return {"status": "ok", "db": "connected", "members_loaded": int(len(data_service.df))}

@app.get("/api/dashboard")
def dashboard():
    df = data_service.df
    population = population_statistics(df)
    # Build outreach status counts from the persisted status file only.
    # Do NOT assume missing statuses are 'Pending' for all members.
    raw_status = getattr(data_service, 'status', {}) or {}
    if raw_status:
        status_counts = {}
        for s in raw_status.values():
            status_counts[s] = status_counts.get(s, 0) + 1
        outreach_status_available = True
    else:
        status_counts = {}
        outreach_status_available = False

    return {
        "total_members": population["total_members"],
        "high_priority_members": population["priority_distribution"]["High Priority"],
        "medium_priority_members": population["priority_distribution"]["Medium Priority"],
        "low_priority_members": population["priority_distribution"]["Low Priority"],
        "average_priority_score": round(float(df.priority_score.mean()), 2),
        "members_with_open_care_gaps": population["members_with_care_gaps"],
        "open_care_gaps": population["total_care_gaps"],
        "outreach_status": {
            "Pending": int(status_counts.get("Pending", 0)),
            "In Progress": int(status_counts.get("In Progress", 0)),
            "Contacted": int(status_counts.get("Contacted", 0)),
            "Follow-up": int(status_counts.get("Follow-up", 0)),
            "Completed": int(status_counts.get("Completed", 0)),
        },
        "outreach_status_available": outreach_status_available,
    }

@app.get("/api/dashboard-insight")
def dashboard_insight():
    result = generate_dashboard_insight()
    return result

@app.get("/api/members")
def members(
    q: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort: str = Query("priority_score_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100)
):
    df = data_service.df.copy()
    if q:
        needle = q.lower()
        df = df[
            df["member_id"].astype(str).str.lower().str.contains(needle) |
            df["member_name"].astype(str).str.lower().str.contains(needle)
        ]
    if priority:
        df = df[df.priority_band.str.lower() == priority.lower()]
    if status:
        df = df[df.member_id.astype(str).map(data_service.get_status).str.lower() == status.lower()]

    if sort == "priority_score_asc":
        df = df.sort_values("priority_score", ascending=True)
    elif sort == "name":
        df = df.sort_values("member_name")
    else:
        df = df.sort_values("priority_score", ascending=False)

    total = len(df)
    start = (page - 1) * page_size
    items = [row_to_member(r) for _, r in df.iloc[start:start+page_size].iterrows()]
    return {"items": items, "page": page, "page_size": page_size, "total": int(total)}

@app.get("/api/priority-queue")
def priority_queue(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    df = data_service.df.sort_values("priority_score", ascending=False)
    total = len(df)
    start = (page - 1) * page_size
    items = [row_to_member(r) for _, r in df.iloc[start:start+page_size].iterrows()]
    return {"items": items, "page": page, "page_size": page_size, "total": int(total)}

@app.get("/api/members/{member_id}")
def member_detail(member_id: str, response: Response):
    row = data_service.row(member_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    response.headers["Cache-Control"] = "no-store"
    explanation = ml_service.explanation(member_id)
    return {
        "member": {
            "member_id": str(row.member_id),
            "member_name": str(row.member_name),
            "age": int(row.age),
            "diabetes": int(row.diabetes),
            "hypertension": int(row.hypertension),
            "heart_disease": int(row.heart_disease),
            "condition_count": int(row.condition_count),
        },
        "priority": {
            "score": round(float(row.priority_score), 2),
            "band": str(row.priority_band),
            "probability": round(float(row.outreach_probability), 4),
        },
        "utilization": {
            "er_visits_30d": int(row.er_visits_30d),
            "hospitalizations_30d": int(row.hospitalizations_30d),
            "outpatient_visits_30d": int(row.outpatient_visits_30d),
            "total_utilization_30d": int(row.total_utilization_30d),
            "acute_utilization_30d": int(row.acute_utilization_30d),
        },
        "care_gaps": {
            "care_gap_count": int(row.care_gap_count),
            "overdue_screening": int(row.overdue_screening),
            "overdue_lab": int(row.overdue_lab),
            "medication_gap": int(row.medication_gap),
        },
        "social_risk": {
            "transportation_barrier": int(row.transportation_barrier),
            "food_insecurity": int(row.food_insecurity),
            "housing_instability": int(row.housing_instability),
            "financial_barrier": int(row.financial_barrier),
            "social_risk_count": int(row.social_risk_count),
        },
        "discharge": {
            "recent_discharge_30d": int(row.recent_discharge_30d),
            "days_since_discharge": None if pd.isna(row.days_since_discharge) else int(row.days_since_discharge),
            "post_discharge_24h": int(row.post_discharge_24h),
        },
        "why_prioritized": explanation,
        "next_best_action": str(row.next_best_action),
        "outreach_status": data_service.get_status(member_id),
    }

@app.get("/api/members/{member_id}/explanation")
def member_explanation(member_id: str):
    if data_service.row(member_id) is None:
        raise HTTPException(status_code=404, detail="Member not found")
    result = ml_service.explanation(member_id)
    return result

@app.get("/api/members/{member_id}/next-action")
def member_next_action(member_id: str):
    row = data_service.row(member_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"member_id": str(member_id), "next_best_action": str(row.next_best_action)}

@app.post("/api/members/{member_id}/call-guide")
def member_call_guide(member_id: str, request: CallGuideRequest = CallGuideRequest()):
    row = data_service.row(member_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    risk_factors = get_risk_factors(row)
    # The discharge feature is a model input, not a dated clinical event record.
    # Keep the call-guide prompt neutral when no verified event date is available.
    guide_risk_factors = [
        "Recent follow-up signal" if factor == "Recent care event signal" else factor
        for factor in risk_factors
    ]
    member_context = {
        "age": int(row.age),
        "conditions": {
            "diabetes": bool(row.diabetes),
            "hypertension": bool(row.hypertension),
            "heart_disease": bool(row.heart_disease),
            "condition_count": int(row.condition_count),
        },
        "utilization_last_30_days": {
            "er_visits": int(row.er_visits_30d),
            "hospitalizations": int(row.hospitalizations_30d),
            "outpatient_visits": int(row.outpatient_visits_30d),
        },
        "care_gaps": {
            "count": int(row.care_gap_count),
            "overdue_screening": bool(row.overdue_screening),
            "overdue_lab": bool(row.overdue_lab),
            "medication_gap": bool(row.medication_gap),
        },
        "social_risk": {
            "transportation_barrier": bool(row.transportation_barrier),
            "food_insecurity": bool(row.food_insecurity),
            "housing_instability": bool(row.housing_instability),
            "financial_barrier": bool(row.financial_barrier),
        },
        "discharge": {
            "recent_follow_up_signal": bool(row.recent_discharge_30d),
            "verified_discharge_date": None,
            "guidance": "The source data contains a follow-up signal but no verified discharge event or date. Do not state or imply a discharge, hospitalization, or specific date. Use this exact neutral question when follow-up is relevant: How have you been feeling since your recent healthcare visit?",
        },
        "risk_factors": guide_risk_factors,
    }
    if request.force_fallback:
        result = fallback_call_guide(
            str(row.member_name), str(row.next_best_action), str(row.priority_band), member_context
        )
    else:
        result = generate_call_guide(
            str(row.member_name),
            str(row.priority_band),
            str(row.next_best_action),
            member_context,
            request.include_questions
        )
    # Echo the resolved row ID rather than the raw path value so the guide
    # response is always tied to the exact member used to build its prompt.
    return {"member_id": str(row.member_id), **result}

@app.patch("/api/members/{member_id}/outreach-status")
def update_outreach_status(member_id: str, payload: OutreachStatusUpdate):
    if data_service.row(member_id) is None:
        raise HTTPException(status_code=404, detail="Member not found")
    try:
        status = data_service.set_status(member_id, payload.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"member_id": str(member_id), "outreach_status": status}

@app.get("/api/analytics")
def analytics(cohort: Optional[str] = Query(None)):
    df = data_service.df
    # Ensure priority_band exists (added during lifespan startup)
    if "priority_band" not in df.columns:
        probs, scores, bands = ml_service.initialize(df)
        df["outreach_probability"] = probs
        df["priority_score"] = scores
        df["priority_band"] = bands
        df["next_best_action"] = df.apply(next_best_action, axis=1)
    if cohort and cohort.lower() != "all":
        df = df[df.priority_band.str.lower() == cohort.lower()]

    total = int(len(df))
    population = population_statistics(df)
    
    # Chronic conditions breakdown
    chronic_conditions = {}
    for col, name in [("hypertension", "Hypertension"), ("diabetes", "Type 2 Diabetes"), ("heart_disease", "Heart Disease")]:
        if col in df.columns:
            cnt = int((df[col] > 0).sum())
            pct = round(cnt / total * 100, 1) if total else 0.0
            chronic_conditions[name] = {"count": cnt, "percentage": pct}
        else:
            chronic_conditions[name] = {"count": None, "percentage": None}
    chronic_conditions["COPD"] = {"count": None, "percentage": None}
    chronic_conditions["CKD (Stages 3-5)"] = {"count": None, "percentage": None}

    # Multimorbidity distribution (0, 1, 2, 3+ conditions)
    multimorbidity = {
        "0 Conditions": int((df["condition_count"] == 0).sum()) if "condition_count" in df.columns else 0,
        "1 Condition": int((df["condition_count"] == 1).sum()) if "condition_count" in df.columns else 0,
        "2 Conditions": int((df["condition_count"] == 2).sum()) if "condition_count" in df.columns else 0,
        "3+ Conditions": int((df["condition_count"] >= 3).sum()) if "condition_count" in df.columns else 0,
    }
    avg_conditions = round(float(df["condition_count"].mean()), 2) if total and "condition_count" in df.columns else 0.0

    # Social Determinants of Health (SDOH)
    sdoh_barriers = [
        ("transportation_barrier", "Transportation Barrier", "transportation"),
        ("food_insecurity", "Food Insecurity", "food_insecurity"),
        ("housing_instability", "Housing Instability", "housing_instability"),
        ("financial_barrier", "Financial Barrier", "financial_barrier"),
    ]
    sdoh_metrics = {}
    sdoh_raw = {}
    for col, label, key in sdoh_barriers:
        if col in df.columns:
            cnt = int((df[col] > 0).sum())
            pct = round(cnt / total * 100, 1) if total else 0.0
            sdoh_metrics[label] = {"count": cnt, "percentage": pct}
            sdoh_raw[key] = cnt
        else:
            sdoh_metrics[label] = {"count": 0, "percentage": 0.0}
            sdoh_raw[key] = 0

    members_with_sdoh = int((df["social_risk_count"] > 0).sum()) if "social_risk_count" in df.columns else 0
    sdoh_distribution = {
        "0 Barriers": int((df["social_risk_count"] == 0).sum()) if "social_risk_count" in df.columns else 0,
        "1 Barrier": int((df["social_risk_count"] == 1).sum()) if "social_risk_count" in df.columns else 0,
        "2 Barriers": int((df["social_risk_count"] == 2).sum()) if "social_risk_count" in df.columns else 0,
        "3+ Barriers": int((df["social_risk_count"] >= 3).sum()) if "social_risk_count" in df.columns else 0,
    }

    # Age Demographics
    age_bins = [
        ("18-34", (df["age"] >= 18) & (df["age"] <= 34)),
        ("35-49", (df["age"] >= 35) & (df["age"] <= 49)),
        ("50-64", (df["age"] >= 50) & (df["age"] <= 64)),
        ("65-74", (df["age"] >= 65) & (df["age"] <= 74)),
        ("75+", df["age"] >= 75),
    ]
    age_groups = []
    for label, mask in age_bins:
        grp_df = df[mask]
        grp_total = int(len(grp_df))
        grp_high = int((grp_df["priority_band"] == "High Priority").sum()) if "priority_band" in grp_df.columns else 0
        grp_gaps = int(grp_df["care_gap_count"].sum()) if "care_gap_count" in grp_df.columns else 0
        age_groups.append({
            "group": label,
            "count": grp_total,
            "percentage": round(grp_total / total * 100, 1) if total else 0.0,
            "high_priority_count": grp_high,
            "total_care_gaps": grp_gaps,
        })
    avg_age = round(float(df["age"].mean()), 1) if total and "age" in df.columns else 0.0

    # Live Outreach Status for this cohort from Database
    member_statuses = [data_service.get_status(mid) for mid in df["member_id"].astype(str)]
    status_series = pd.Series(member_statuses)
    status_counts = {
        "Pending": int((status_series == "Pending").sum()),
        "In Progress": int((status_series == "In Progress").sum()),
        "Contacted": int((status_series == "Contacted").sum()),
        "Follow-up": int((status_series == "Follow-up").sum()),
        "Completed": int((status_series == "Completed").sum()),
    }
    engaged_count = total - status_counts["Pending"]
    engagement_rate = round(engaged_count / total * 100, 1) if total else 0.0
    completion_rate = round(status_counts["Completed"] / total * 100, 1) if total else 0.0

    # Transitional Care & Post-Discharge
    recent_discharge_count = int((df["recent_discharge_30d"] == 1).sum()) if "recent_discharge_30d" in df.columns else 0
    post_discharge_24h_count = int((df["post_discharge_24h"] == 1).sum()) if "post_discharge_24h" in df.columns else 0
    discharge_with_gap_count = int(((df["recent_discharge_30d"] == 1) & (df["care_gap_count"] > 0)).sum()) if ("recent_discharge_30d" in df.columns and "care_gap_count" in df.columns) else 0
    acute_utilization_total = int(df["er_visits_30d"].sum() + df["hospitalizations_30d"].sum()) if ("er_visits_30d" in df.columns and "hospitalizations_30d" in df.columns) else 0

    # 1. Priority Score Statistics & Histogram Distribution (0-10, 10-20, ..., 90-100)
    score_col = df["priority_score"] if "priority_score" in df.columns else pd.Series([0])
    score_min = round(float(score_col.min()), 2) if len(score_col) else 0.0
    score_avg = round(float(score_col.mean()), 2) if len(score_col) else 0.0
    score_max = round(float(score_col.max()), 2) if len(score_col) else 0.0

    score_ranges = [
        ("0-10", 0, 10, True),
        ("10-20", 10, 20, False),
        ("20-30", 20, 30, False),
        ("30-40", 30, 40, False),
        ("40-50", 40, 50, False),
        ("50-60", 50, 60, False),
        ("60-70", 60, 70, False),
        ("70-80", 70, 80, False),
        ("80-90", 80, 90, False),
        ("90-100", 90, 100, False),
    ]
    score_distribution = []
    for label, low, high, is_first in score_ranges:
        if is_first:
            cnt = int(((score_col >= low) & (score_col <= high)).sum())
        else:
            cnt = int(((score_col > low) & (score_col <= high)).sum())
        pct = round((cnt / total) * 100, 1) if total else 0.0
        score_distribution.append({
            "range": label,
            "count": cnt,
            "percentage": pct
        })

    # 2. Recommended Next Actions (Grouped by next_best_action, count & percentage sorted desc)
    recommended_actions = []
    if "next_best_action" in df.columns:
        nba_series = df["next_best_action"].value_counts()
        for act_name, act_cnt in nba_series.items():
            act_cnt_int = int(act_cnt)
            act_pct = round((act_cnt_int / total) * 100, 1) if total else 0.0
            recommended_actions.append({
                "action": str(act_name),
                "count": act_cnt_int,
                "percentage": act_pct,
            })

    # 3. Common Factors Mentioned in Priority Explanations
    explanation_factors_raw = [
        ("Recent Acute Utilization", int(((df["er_visits_30d"] > 0) | (df["hospitalizations_30d"] > 0)).sum()) if ("er_visits_30d" in df.columns and "hospitalizations_30d" in df.columns) else 0),
        ("Open Care Gap Burden", int((df["care_gap_count"] > 0).sum()) if "care_gap_count" in df.columns else 0),
        ("Chronic Condition Complexity (2+)", int((df["condition_count"] >= 2).sum()) if "condition_count" in df.columns else 0),
        ("Medication Adherence Gap", int((df["medication_gap"] > 0).sum()) if "medication_gap" in df.columns else 0),
        ("Recent Post-Discharge Care Event", int((df["recent_discharge_30d"] == 1).sum()) if "recent_discharge_30d" in df.columns else 0),
        ("Social-Support & Environmental Barriers", int((df["social_risk_count"] > 0).sum()) if "social_risk_count" in df.columns else 0),
        ("Senior Age Demographic (65+)", int((df["age"] >= 65).sum()) if "age" in df.columns else 0),
    ]
    explanation_factors_raw.sort(key=lambda x: x[1], reverse=True)
    priority_explanation_factors = [
        {
            "factor": factor_name,
            "count": factor_count,
            "percentage": round((factor_count / total) * 100, 1) if total else 0.0,
        }
        for factor_name, factor_count in explanation_factors_raw
    ]

    # Care gap categories
    care_gap_categories = [
        {
            "category": "Overdue Screening",
            "field": "overdue_screening",
            "total_identified": int((df["overdue_screening"] > 0).sum()),
            "open_count": int((df["overdue_screening"] > 0).sum()),
            "percentage": round(int((df["overdue_screening"] > 0).sum()) / total * 100, 1) if total else 0.0,
            "closed_count": None,
            "closure_rate": None,
        },
        {
            "category": "Overdue Lab",
            "field": "overdue_lab",
            "total_identified": int((df["overdue_lab"] > 0).sum()),
            "open_count": int((df["overdue_lab"] > 0).sum()),
            "percentage": round(int((df["overdue_lab"] > 0).sum()) / total * 100, 1) if total else 0.0,
            "closed_count": None,
            "closure_rate": None,
        },
        {
            "category": "Medication Gap",
            "field": "medication_gap",
            "total_identified": int((df["medication_gap"] > 0).sum()),
            "open_count": int((df["medication_gap"] > 0).sum()),
            "percentage": round(int((df["medication_gap"] > 0).sum()) / total * 100, 1) if total else 0.0,
            "closed_count": None,
            "closure_rate": None,
        },
    ]

    return {
        "scope": "Current Database",
        "dataset_name": "final_member_dataset.csv",
        "total_members": total,
        "priority_score": {
            "min": score_min,
            "average": score_avg,
            "max": score_max,
            "distribution": score_distribution,
        },
        "recommended_actions": recommended_actions,
        "priority_explanation_factors": priority_explanation_factors,
        "priority_distribution": population["priority_distribution"],
        "average_priority_score": score_avg,
        "utilization": {
            **utilization_statistics(df),
            "acute_utilization_total": acute_utilization_total,
        },
        "chronic_conditions": chronic_conditions,
        "multimorbidity": {
            "distribution": multimorbidity,
            "average_conditions": avg_conditions,
        },
        "care_gaps": {
            "members_with_care_gaps": population["members_with_care_gaps"],
            "total_care_gaps": population["total_care_gaps"],
            "members_with_overdue_screening": population["members_with_overdue_screening"],
            "members_with_overdue_lab": population["members_with_overdue_lab"],
            "members_with_medication_gap": population["members_with_medication_gap"],
            "categories": care_gap_categories,
        },
        "social_determinants": {
            "barriers": sdoh_metrics,
            "members_with_sdoh": members_with_sdoh,
            "sdoh_prevalence_pct": round(members_with_sdoh / total * 100, 1) if total else 0.0,
            "distribution": sdoh_distribution,
        },
        "social_risk": sdoh_raw,
        "age_demographics": {
            "average_age": avg_age,
            "groups": age_groups,
        },
        "outreach_pipeline": {
            "status_counts": status_counts,
            "engaged_count": engaged_count,
            "engagement_rate": engagement_rate,
            "completion_rate": completion_rate,
        },
        "transitional_care": {
            "recent_discharge_count": recent_discharge_count,
            "post_discharge_24h_count": post_discharge_24h_count,
            "discharge_with_gap_count": discharge_with_gap_count,
        },
        "next_best_actions": {act["action"]: act["count"] for act in recommended_actions},
        "available_cohorts": ["All Cohorts", "High Priority", "Medium Priority", "Low Priority"],
    }

@app.get("/analytics/summary")
@app.get("/api/analytics/summary")
def analytics_summary(cohort: Optional[str] = Query(None)):
    return analytics(cohort=cohort)

@app.get("/api/model-performance")
def model_performance():
    return {
        "selected_model": "Logistic Regression",
        "selection_metric": "F1",
        "models": ml_service.metrics.to_dict(orient="records")
    }


@app.get('/api/outreach-status')
def outreach_status():
    # Return persisted outreach status counts (do not assume default values for missing statuses)
    raw_status = getattr(data_service, 'status', {}) or {}
    if not raw_status:
        return {"outreach_status_available": False, "outreach_status": {}, "total_members": int(len(data_service.df))}
    counts = {}
    for v in raw_status.values():
        counts[v] = counts.get(v, 0) + 1
    return {"outreach_status_available": True, "outreach_status": counts, "total_members": int(len(data_service.df))}
