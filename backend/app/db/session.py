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


from sqlalchemy.pool import NullPool

def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # If running in serverless environment (Vercel, AWS Lambda) where root is read-only
        if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            tmp_db = Path("/tmp/carewise.db")
            seed_db = DATA_DIR / "carewise.db"
            if not tmp_db.exists() and seed_db.exists():
                import shutil
                try:
                    shutil.copy2(seed_db, tmp_db)
                except Exception:
                    pass
            db_url = f"sqlite:///{tmp_db.as_posix()}"
        else:
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
    # Supabase PostgreSQL or MySQL
    if "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL:
        connect_args["sslmode"] = "require"
    
    # Use NullPool on serverless so connections close immediately
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 300
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10

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
