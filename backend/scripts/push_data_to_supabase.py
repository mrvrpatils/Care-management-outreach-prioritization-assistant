import sys
import os
import argparse
import json
import sqlite3
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.db.models import Base, MemberModel, OutreachStatusModel, CampaignModel, LoginModel
from app.services.auth_service import hash_password

DATA_DIR = BACKEND_DIR / "data"
SQLITE_DB = DATA_DIR / "carewise.db"
CSV_FILE = DATA_DIR / "final_member_dataset.csv"
STATUS_FILE = DATA_DIR / "outreach_status.json"


def normalize_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def push_to_supabase(target_db_url: str):
    target_db_url = normalize_postgres_url(target_db_url)
    display_url = target_db_url.split("@")[-1] if "@" in target_db_url else "Target DB"
    print("\n========================================================")
    print(f" Connecting to Supabase: {display_url}")
    print("========================================================")

    engine = create_engine(
        target_db_url,
        pool_pre_ping=True,
        pool_recycle=300
    )

    # 1. Create schema/tables in Supabase
    print("[1/5] Creating tables in Supabase...")
    Base.metadata.create_all(bind=engine)
    print("      Tables (members, outreach_statuses, campaigns, login) ready.")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 2. Push Members
        print("\n[2/5] Pushing members data...")
        df_members = None
        if SQLITE_DB.exists():
            try:
                conn = sqlite3.connect(SQLITE_DB)
                df_members = pd.read_sql("SELECT * FROM members ORDER BY member_id", conn)
                conn.close()
            except Exception as e:
                print(f"      Warning: could not read from SQLite: {e}")

        if (df_members is None or df_members.empty) and CSV_FILE.exists():
            df_members = pd.read_csv(CSV_FILE)

        if df_members is not None and not df_members.empty:
            existing_members = session.query(MemberModel).count()
            if existing_members > 0:
                print(f"      Supabase already has {existing_members} members. Clearing before full sync...")
                session.query(MemberModel).delete()
                session.commit()

            # Clean nulls
            df_members["days_since_discharge"] = df_members["days_since_discharge"].astype(object).where(
                pd.notnull(df_members["days_since_discharge"]), None
            )

            total_members = len(df_members)
            batch_size = 1000
            print(f"      Inserting {total_members} members in batches of {batch_size}...")

            for start in range(0, total_members, batch_size):
                batch_df = df_members.iloc[start:start + batch_size]
                records = []
                for _, row in batch_df.iterrows():
                    records.append(
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
                session.bulk_save_objects(records)
                session.commit()
                print(f"      Pushed {min(start + batch_size, total_members)} / {total_members} members.")
        else:
            print("      No members data found to push.")

        # 3. Push Outreach Statuses
        print("\n[3/5] Pushing outreach statuses...")
        statuses = {}
        if SQLITE_DB.exists():
            try:
                conn = sqlite3.connect(SQLITE_DB)
                cur = conn.cursor()
                rows = cur.execute("SELECT member_id, status FROM outreach_statuses").fetchall()
                statuses = {r[0]: r[1] for r in rows}
                conn.close()
            except Exception:
                pass

        if not statuses and STATUS_FILE.exists():
            try:
                statuses = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            except Exception:
                statuses = {}

        if statuses:
            existing_statuses = session.query(OutreachStatusModel).count()
            if existing_statuses > 0:
                print(f"      Supabase already has {existing_statuses} statuses. Clearing before sync...")
                session.query(OutreachStatusModel).delete()
                session.commit()

            items = list(statuses.items())
            total_statuses = len(items)
            batch_size = 1000
            print(f"      Inserting {total_statuses} outreach statuses in batches of {batch_size}...")

            for start in range(0, total_statuses, batch_size):
                batch_items = items[start:start + batch_size]
                records = [
                    OutreachStatusModel(member_id=str(mid), status=str(st))
                    for mid, st in batch_items
                ]
                session.bulk_save_objects(records)
                session.commit()
                print(f"      Pushed {min(start + batch_size, total_statuses)} / {total_statuses} statuses.")
        else:
            print("      No outreach statuses found to push.")

        # 4. Push Campaigns
        print("\n[4/5] Pushing campaigns...")
        campaign_records = []
        if SQLITE_DB.exists():
            try:
                conn = sqlite3.connect(SQLITE_DB)
                cur = conn.cursor()
                rows = cur.execute("SELECT campaign_id, field, initiator, member_count, members_sample_json FROM campaigns").fetchall()
                for r in rows:
                    campaign_records.append(
                        CampaignModel(
                            campaign_id=str(r[0]),
                            field=str(r[1]),
                            initiator=str(r[2]) if r[2] else None,
                            member_count=int(r[3]),
                            members_sample_json=str(r[4]) if r[4] else None,
                        )
                    )
                conn.close()
            except Exception:
                pass

        if campaign_records:
            for camp in campaign_records:
                existing = session.query(CampaignModel).filter(CampaignModel.campaign_id == camp.campaign_id).first()
                if not existing:
                    session.add(camp)
            session.commit()
            print(f"      Pushed {len(campaign_records)} campaign(s).")
        else:
            print("      No existing campaigns to push.")

        # 5. Push Login Users
        print("\n[5/5] Pushing authentication users...")
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
        for u in demo_users:
            existing = session.query(LoginModel).filter(LoginModel.username == u.username).first()
            if not existing:
                session.add(u)
        session.commit()
        print("      Admin and Care Manager user accounts configured.")

        # Final Verification
        print("\n========================================================")
        print(" VERIFICATION SUMMARY IN SUPABASE")
        print("========================================================")
        count_members = session.query(MemberModel).count()
        count_statuses = session.query(OutreachStatusModel).count()
        count_campaigns = session.query(CampaignModel).count()
        count_users = session.query(LoginModel).count()

        print(f" Members table:           {count_members:,} records")
        print(f" Outreach statuses table: {count_statuses:,} records")
        print(f" Campaigns table:         {count_campaigns:,} records")
        print(f" Login accounts table:    {count_users:,} records")
        print("========================================================")
        print(" SUCCESS! Supabase PostgreSQL database is fully populated and ready for cloud deployment.")

    except Exception as e:
        session.rollback()
        print(f"\n Error during Supabase upload: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload database data into Supabase PostgreSQL")
    parser.add_argument(
        "--target-url",
        type=str,
        default=os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL"),
        help="Supabase Postgres database connection string (URI)"
    )
    args = parser.parse_args()

    if not args.target_url or "sqlite" in args.target_url or "localhost" in args.target_url:
        print("\n Please provide a valid Supabase PostgreSQL connection URI.")
        print("Usage example:")
        print('  python backend/scripts/push_data_to_supabase.py --target-url "postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"\n')
        sys.exit(1)

    push_to_supabase(args.target_url)
