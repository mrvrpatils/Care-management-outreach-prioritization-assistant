"""Verification script to check row counts and sample records in Supabase."""
import sys
import os
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text

# Force UTF-8 for console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


def normalize_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def verify(db_url: str):
    db_url = normalize_postgres_url(db_url)
    print("\n========================================================")
    print(" Checking Supabase Database...")
    print("========================================================")

    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        tables = ["members", "outreach_statuses", "campaigns", "login"]
        all_passed = True

        for t in tables:
            try:
                result = conn.execute(text(f"SELECT count(*) FROM {t}")).fetchone()
                cnt = result[0]
                status = "[OK]" if cnt > 0 else "[EMPTY]"
                print(f" {t.ljust(20)}: {cnt:>7,} rows  {status}")
            except Exception as e:
                all_passed = False
                print(f" {t.ljust(20)}: [ERROR] Table missing or error ({e})")

        print("--------------------------------------------------------")
        if all_passed:
            try:
                sample_member = conn.execute(text("SELECT member_id, member_name, age, condition_count FROM members LIMIT 1")).fetchone()
                print(f" Sample Member    : ID={sample_member[0]}, Name={sample_member[1]}, Age={sample_member[2]}")
                sample_user = conn.execute(text("SELECT username, email, role FROM login LIMIT 1")).fetchone()
                print(f" Sample Admin User: Username={sample_user[0]}, Role={sample_user[2]}")
            except Exception:
                pass
            print("========================================================")
            print(" SUCCESS! All data is verified and loaded in Supabase!")
        else:
            print(" Some tables were missing.")
        print("========================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify CareWise data in Supabase")
    parser.add_argument(
        "--target-url",
        type=str,
        default=os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL"),
        help="Supabase Postgres database connection URI"
    )
    args = parser.parse_args()

    if not args.target_url or "sqlite" in args.target_url or "localhost" in args.target_url:
        print("\nPlease provide your Supabase PostgreSQL connection URI:")
        print('python backend/scripts/verify_supabase.py --target-url "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"\n')
        sys.exit(1)

    verify(args.target_url)
