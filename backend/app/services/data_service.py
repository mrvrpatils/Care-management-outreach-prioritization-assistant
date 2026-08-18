from pathlib import Path
import hashlib
import json
import pandas as pd
from ..db.session import engine, SessionLocal
from ..db.models import MemberModel, OutreachStatusModel
from ..db.init_db import init_db

BASE = Path(__file__).resolve().parents[2]
DATA_PATH = BASE / "data" / "final_member_dataset.csv"
STATUS_PATH = BASE / "data" / "outreach_status.json"

STATUS_VALUES = {"Pending", "In Progress", "Contacted", "Follow-up", "Completed"}


def utilization_statistics(df: pd.DataFrame) -> dict[str, int | float]:
    """Return the canonical 30-day utilization aggregates for a dataset scope."""
    total_members = int(len(df))
    return {
        "members_with_er_visits_30d": int((df["er_visits_30d"] > 0).sum()),
        "members_with_hospitalizations_30d": int((df["hospitalizations_30d"] > 0).sum()),
        "members_with_outpatient_visits_30d": int((df["outpatient_visits_30d"] > 0).sum()),
        "average_er_visits_30d": round(float(df["er_visits_30d"].mean()), 2) if total_members else 0.0,
        "average_hospitalizations_30d": round(float(df["hospitalizations_30d"].mean()), 2) if total_members else 0.0,
        "average_outpatient_visits_30d": round(float(df["outpatient_visits_30d"].mean()), 2) if total_members else 0.0,
        "total_er_visits_30d": int(df["er_visits_30d"].sum()),
        "total_hospitalizations_30d": int(df["hospitalizations_30d"].sum()),
        "total_outpatient_visits_30d": int(df["outpatient_visits_30d"].sum()),
    }


def population_statistics(df: pd.DataFrame) -> dict[str, object]:
    """Return the canonical population and care-gap aggregates for a scope."""
    priority_distribution = df["priority_band"].value_counts().to_dict()
    return {
        "total_members": int(len(df)),
        "priority_distribution": {
            "High Priority": int(priority_distribution.get("High Priority", 0)),
            "Medium Priority": int(priority_distribution.get("Medium Priority", 0)),
            "Low Priority": int(priority_distribution.get("Low Priority", 0)),
        },
        "members_with_care_gaps": int((df["care_gap_count"] > 0).sum()),
        "total_care_gaps": int(df["care_gap_count"].sum()),
        "members_with_overdue_screening": int((df["overdue_screening"] > 0).sum()),
        "members_with_overdue_lab": int((df["overdue_lab"] > 0).sum()),
        "members_with_medication_gap": int((df["medication_gap"] > 0).sum()),
    }


def _deterministic_status(member_id):
    digest = hashlib.sha256(str(member_id).encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 38:
        return "Pending"
    if bucket < 53:
        return "In Progress"
    if bucket < 68:
        return "Contacted"
    if bucket < 85:
        return "Follow-up"
    return "Completed"


class DataService:
    def __init__(self):
        # Ensure database tables exist and are seeded
        init_db()

        # Load member dataset from database (or CSV fallback)
        try:
            with engine.connect() as conn:
                self.df = pd.read_sql("SELECT * FROM members ORDER BY member_id", conn)
        except Exception:
            self.df = pd.DataFrame()

        if self.df.empty and DATA_PATH.exists():
            self.df = pd.read_csv(DATA_PATH)

        self.df["days_since_discharge"] = self.df["days_since_discharge"].astype("float")
        self.df["total_utilization_30d"] = (
            self.df["er_visits_30d"] + self.df["hospitalizations_30d"] +
            self.df["outpatient_visits_30d"]
        )
        self.df["acute_utilization_30d"] = (
            self.df["er_visits_30d"] + self.df["hospitalizations_30d"]
        )
        self.df["social_risk_count"] = self.df[
            ["transportation_barrier", "food_insecurity", "housing_instability", "financial_barrier"]
        ].sum(axis=1)
        self.df["post_discharge_24h"] = (
            (self.df["recent_discharge_30d"] == 1) &
            (self.df["days_since_discharge"] == 0)
        ).astype(int)
        self.df["clinical_burden"] = self.df["condition_count"]
        self.df["care_gap_burden"] = self.df["care_gap_count"]

        # Load outreach statuses from Database
        self.status = {}
        self.load_status_from_db()

    def load_status_from_db(self):
        db = SessionLocal()
        try:
            records = db.query(OutreachStatusModel).all()
            if records:
                self.status = {r.member_id: r.status for r in records}
            else:
                # If DB outreach_statuses is empty, check JSON fallback
                if STATUS_PATH.exists():
                    try:
                        self.status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
                    except Exception:
                        self.status = {}
                else:
                    self.status = {}
                if self.status:
                    db_records = [OutreachStatusModel(member_id=k, status=v) for k, v in self.status.items()]
                    db.bulk_save_objects(db_records)
                    db.commit()
        finally:
            db.close()

    def save_status(self):
        try:
            STATUS_PATH.write_text(json.dumps(self.status, indent=2), encoding="utf-8")
        except Exception:
            pass

    def seed_statuses_if_empty(self):
        if not self.status:
            for mid in self.df["member_id"].astype(str):
                self.status[mid] = _deterministic_status(mid)
            self.sync_all_statuses_to_db()
            self.save_status()
            return
        existing_ids = set(self.status.keys())
        needed = False
        for mid in self.df["member_id"].astype(str):
            if mid not in existing_ids:
                self.status[mid] = _deterministic_status(mid)
                needed = True
        if needed:
            self.sync_all_statuses_to_db()
            self.save_status()

    def sync_all_statuses_to_db(self):
        db = SessionLocal()
        try:
            db.query(OutreachStatusModel).delete()
            db_records = [OutreachStatusModel(member_id=k, status=v) for k, v in self.status.items()]
            db.bulk_save_objects(db_records)
            db.commit()
        finally:
            db.close()

    def get_status(self, member_id):
        return self.status.get(str(member_id), "Pending")

    def set_status(self, member_id, status):
        if status not in STATUS_VALUES:
            raise ValueError(f"Invalid status. Use one of: {sorted(STATUS_VALUES)}")
        mid = str(member_id)
        self.status[mid] = status

        # Persist to database
        db = SessionLocal()
        try:
            record = db.query(OutreachStatusModel).filter(OutreachStatusModel.member_id == mid).first()
            if record:
                record.status = status
            else:
                record = OutreachStatusModel(member_id=mid, status=status)
                db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        self.save_status()
        return status

    def row(self, member_id):
        rows = self.df[self.df["member_id"].astype(str) == str(member_id)]
        return None if rows.empty else rows.iloc[0]


data_service = DataService()
