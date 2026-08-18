import sys
import os
import json
import sqlite3
from pathlib import Path
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.auth_service import hash_password

DATA_DIR = BACKEND_DIR / "data"
SQLITE_DB = DATA_DIR / "carewise.db"
CSV_FILE = DATA_DIR / "final_member_dataset.csv"
STATUS_FILE = DATA_DIR / "outreach_status.json"
OUTPUT_SQL = BACKEND_DIR / "scripts" / "supabase_setup.sql"

def generate_sql():
    lines = []
    lines.append("-- ========================================================")
    lines.append("-- Care Management Outreach Prioritization Assistant - Supabase PostgreSQL Setup & Data")
    lines.append("-- Run this script in the Supabase Dashboard -> SQL Editor")
    lines.append("-- ========================================================\n")

    # 1. Create Tables
    lines.append("-- 1. Create Tables")
    lines.append("""
CREATE TABLE IF NOT EXISTS members (
    member_id VARCHAR(50) PRIMARY KEY,
    member_name VARCHAR(200) NOT NULL,
    age INTEGER NOT NULL DEFAULT 0,
    condition_count INTEGER NOT NULL DEFAULT 0,
    diabetes INTEGER NOT NULL DEFAULT 0,
    hypertension INTEGER NOT NULL DEFAULT 0,
    heart_disease INTEGER NOT NULL DEFAULT 0,
    er_visits_30d INTEGER NOT NULL DEFAULT 0,
    hospitalizations_30d INTEGER NOT NULL DEFAULT 0,
    outpatient_visits_30d INTEGER NOT NULL DEFAULT 0,
    recent_discharge_30d INTEGER NOT NULL DEFAULT 0,
    days_since_discharge DOUBLE PRECISION,
    care_gap_count INTEGER NOT NULL DEFAULT 0,
    overdue_screening INTEGER NOT NULL DEFAULT 0,
    overdue_lab INTEGER NOT NULL DEFAULT 0,
    medication_gap INTEGER NOT NULL DEFAULT 0,
    transportation_barrier INTEGER NOT NULL DEFAULT 0,
    food_insecurity INTEGER NOT NULL DEFAULT 0,
    housing_instability INTEGER NOT NULL DEFAULT 0,
    financial_barrier INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS outreach_statuses (
    member_id VARCHAR(50) PRIMARY KEY REFERENCES members(member_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gap_type VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    target_count INTEGER NOT NULL DEFAULT 0,
    reached_count INTEGER NOT NULL DEFAULT 0,
    closed_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(200),
    role VARCHAR(100) DEFAULT 'Care Manager',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
""")

    # 2. Insert Login Users
    lines.append("-- 2. Seed Login Accounts")
    admin_pw = hash_password("admin123")
    cm_pw = hash_password("password123")
    lines.append(f"""
INSERT INTO login (username, password_hash, email, full_name, role)
VALUES 
    ('admin', '{admin_pw}', 'admin@careoutreach.health', 'Dr. Sarah Mitchell', 'Administrator'),
    ('caremanager', '{cm_pw}', 'caremanager@careoutreach.health', 'Elena Rostova', 'Lead Care Manager')
ON CONFLICT (username) DO NOTHING;
""")

    # 3. Insert Members
    lines.append("-- 3. Seed Members (10,000 records)")
    df = None
    if SQLITE_DB.exists():
        try:
            conn = sqlite3.connect(SQLITE_DB)
            df = pd.read_sql("SELECT * FROM members ORDER BY member_id", conn)
            conn.close()
        except Exception:
            pass
    if (df is None or df.empty) and CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE)

    if df is not None and not df.empty:
        batch_size = 500
        for i in range(0, len(df), batch_size):
            chunk = df.iloc[i:i + batch_size]
            val_rows = []
            for _, r in chunk.iterrows():
                m_id = str(r["member_id"]).replace("'", "''")
                m_name = str(r["member_name"]).replace("'", "''")
                dsd = "NULL" if pd.isna(r["days_since_discharge"]) else str(float(r["days_since_discharge"]))
                val_rows.append(
                    f"('{m_id}', '{m_name}', {int(r['age'])}, {int(r['condition_count'])}, {int(r['diabetes'])}, "
                    f"{int(r['hypertension'])}, {int(r['heart_disease'])}, {int(r['er_visits_30d'])}, "
                    f"{int(r['hospitalizations_30d'])}, {int(r['outpatient_visits_30d'])}, {int(r['recent_discharge_30d'])}, "
                    f"{dsd}, {int(r['care_gap_count'])}, {int(r['overdue_screening'])}, {int(r['overdue_lab'])}, "
                    f"{int(r['medication_gap'])}, {int(r['transportation_barrier'])}, {int(r['food_insecurity'])}, "
                    f"{int(r['housing_instability'])}, {int(r['financial_barrier'])})"
                )
            lines.append("INSERT INTO members (member_id, member_name, age, condition_count, diabetes, hypertension, heart_disease, er_visits_30d, hospitalizations_30d, outpatient_visits_30d, recent_discharge_30d, days_since_discharge, care_gap_count, overdue_screening, overdue_lab, medication_gap, transportation_barrier, food_insecurity, housing_instability, financial_barrier) VALUES\n" + ",\n".join(val_rows) + "\nON CONFLICT (member_id) DO NOTHING;\n")

    # 4. Insert Outreach Statuses
    lines.append("-- 4. Seed Outreach Statuses (10,000 records)")
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
        items = list(statuses.items())
        batch_size = 500
        for i in range(0, len(items), batch_size):
            chunk = items[i:i + batch_size]
            val_rows = [f"('{str(k).replace("'", "''")}', '{str(v).replace("'", "''")}')" for k, v in chunk]
            lines.append("INSERT INTO outreach_statuses (member_id, status) VALUES\n" + ",\n".join(val_rows) + "\nON CONFLICT (member_id) DO NOTHING;\n")

    # 5. Insert Campaigns
    lines.append("-- 5. Seed Campaigns")
    if SQLITE_DB.exists():
        try:
            conn = sqlite3.connect(SQLITE_DB)
            cur = conn.cursor()
            rows = cur.execute("SELECT campaign_id, field, initiator, member_count, members_sample_json FROM campaigns").fetchall()
            if rows:
                val_rows = []
                for r in rows:
                    c_id = str(r[0]).replace("'", "''")
                    fld = str(r[1]).replace("'", "''")
                    init = f"'{str(r[2]).replace("'", "''")}'" if r[2] else "NULL"
                    cnt = int(r[3])
                    smp = f"'{str(r[4]).replace("'", "''")}'" if r[4] else "NULL"
                    val_rows.append(f"('{c_id}', '{fld}', {init}, {cnt}, {smp})")
                lines.append("INSERT INTO campaigns (campaign_id, field, initiator, member_count, members_sample_json) VALUES\n" + ",\n".join(val_rows) + "\nON CONFLICT (campaign_id) DO NOTHING;\n")
            conn.close()
        except Exception:
            pass

    OUTPUT_SQL.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated SQL migration file: {OUTPUT_SQL} ({OUTPUT_SQL.stat().st_size:,} bytes)")

if __name__ == "__main__":
    generate_sql()
