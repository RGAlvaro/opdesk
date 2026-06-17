"""SQLAlchemy engine, session factory, and FastAPI database dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create the SQLAlchemy engine, optionally overriding the configured URL."""
    url = database_url or get_settings().database_url
    return create_engine(url, pool_pre_ping=True)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
