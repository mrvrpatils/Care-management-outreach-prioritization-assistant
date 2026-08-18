"""Database initialization and seeding helper script."""
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.db.init_db import init_db
from app.db.session import engine, DATABASE_URL

if __name__ == "__main__":
    print(f"Connecting to database: {DATABASE_URL}")
    init_db()
    print("Database initialized and seeded successfully.")
