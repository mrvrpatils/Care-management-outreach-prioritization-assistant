import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"

# Load environment variables from .env
PRIMARY_ENV = BACKEND_DIR / ".env"
CI_ENV = BACKEND_DIR / "ci" / ".env"
load_dotenv(PRIMARY_ENV if PRIMARY_ENV.is_file() else CI_ENV)


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_path = DATA_DIR / "carewise.db"
        db_url = f"sqlite:///{db_path.as_posix()}"
    elif db_url.startswith("postgres://"):
        # Fix legacy postgres:// URL scheme for SQLAlchemy 2.x
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return db_url


DATABASE_URL = get_database_url()

connect_args = {}
engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs["pool_pre_ping"] = False
else:
    # MySQL Workbench or Supabase PostgreSQL
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
