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
    return db_url


DATABASE_URL = get_database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True if not DATABASE_URL.startswith("sqlite") else False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
