from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Use a default URL if not provided, or use sqlite for local dev if postgres is not ready
# For this task, I'll assume PostgreSQL as requested, but fallback to sqlite if env var is missing for easier testing
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./devpulse.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
