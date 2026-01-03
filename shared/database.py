import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Use a default path but allow override
DB_PATH = os.getenv("GEMINI_DB_PATH", "gemini.db")

# Create engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(path: Path = None):
    global engine
    if path:
        db_url = f"sqlite:///{path}"
        engine = create_engine(db_url, echo=False)
        SessionLocal.configure(bind=engine)
    
    Base.metadata.create_all(bind=engine)
