"""
Database configuration and session management for GIKI Nexus Teammate Finder.
Uses SQLite via SQLAlchemy 2.0 with connection pooling and dependency injection.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

# SQLite connection args
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_instance=None) -> None:
    """Initialize database tables."""
    target_engine = engine_instance or engine
    Base.metadata.create_all(bind=target_engine)
