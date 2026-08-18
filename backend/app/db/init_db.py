from pathlib import Path
import json
import pandas as pd
from .session import engine, SessionLocal, Base
from .models import MemberModel, OutreachStatusModel, LoginModel
from ..services.auth_service import hash_password

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BACKEND_DIR / "data" / "final_member_dataset.csv"
STATUS_PATH = BACKEND_DIR / "data" / "outreach_status.json"


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed members if empty
        member_count = db.query(MemberModel).count()
        if member_count == 0 and DATA_PATH.exists():
            df = pd.read_csv(DATA_PATH)
            # Fill NaN for nullable fields
            df["days_since_discharge"] = df["days_since_discharge"].astype(object).where(pd.notnull(df["days_since_discharge"]), None)
            
            member_records = []
            for _, row in df.iterrows():
                member_records.append(
                    MemberModel(
                        member_id=str(row["member_id"]),
                        member_name=str(row["member_name"]),
                        age=int(row["age"]),
                        condition_count=int(row["condition_count"]),
                        diabetes=int(row["diabetes"]),
                        hypertension=int(row["hypertension"]),
                        heart_disease=int(row["heart_disease"]),
                        er_visits_30d=int(row["er_visits_30d"]),
                        hospitalizations_30d=int(row["hospitalizations_30d"]),
                        outpatient_visits_30d=int(row["outpatient_visits_30d"]),
                        recent_discharge_30d=int(row["recent_discharge_30d"]),
                        days_since_discharge=None if pd.isna(row["days_since_discharge"]) else float(row["days_since_discharge"]),
                        care_gap_count=int(row["care_gap_count"]),
                        overdue_screening=int(row["overdue_screening"]),
                        overdue_lab=int(row["overdue_lab"]),
                        medication_gap=int(row["medication_gap"]),
                        transportation_barrier=int(row["transportation_barrier"]),
                        food_insecurity=int(row["food_insecurity"]),
                        housing_instability=int(row["housing_instability"]),
                        financial_barrier=int(row["financial_barrier"]),
                    )
                )
            if member_records:
                db.bulk_save_objects(member_records)
                db.commit()
                print(f"[DB] Initialized and seeded {len(member_records)} members from CSV.")

        # 2. Seed outreach statuses if empty
        status_count = db.query(OutreachStatusModel).count()
        if status_count == 0:
            status_data = {}
            if STATUS_PATH.exists():
                try:
                    status_data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
                except Exception:
                    status_data = {}
            
            if status_data:
                status_records = [
                    OutreachStatusModel(member_id=str(mid), status=str(st))
                    for mid, st in status_data.items()
                ]
                db.bulk_save_objects(status_records)
                db.commit()
                print(f"[DB] Initialized and seeded {len(status_records)} outreach statuses from JSON.")

        # 3. Seed default login users if empty
        login_count = db.query(LoginModel).count()
        if login_count == 0:
            demo_users = [
                LoginModel(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    email="admin@careoutreach.health",
                    full_name="Dr. Sarah Mitchell",
                    role="Administrator"
                ),
                LoginModel(
                    username="caremanager",
                    password_hash=hash_password("password123"),
                    email="caremanager@careoutreach.health",
                    full_name="Elena Rostova",
                    role="Lead Care Manager"
                )
            ]
            db.add_all(demo_users)
            db.commit()
            print("[DB] Initialized and seeded default users into login table.")

    finally:
        db.close()



if __name__ == "__main__":
    init_db()
    print("[DB] Database schema and seeding complete.")
