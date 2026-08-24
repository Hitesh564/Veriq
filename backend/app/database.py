from sqlmodel import create_engine, Session
from app.config import DATABASE_URL

# Connect arguments specifically for SQLite thread handling
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def get_session():
    """FastAPI dependency yielding a database session."""
    with Session(engine) as session:
        yield session

def get_direct_session():
    """Direct session factory for background tasks or standalone scripts."""
    return Session(engine)
