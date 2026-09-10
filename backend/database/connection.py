"""
backend/database/connection.py

SQLAlchemy 2.x database engine, session factory, and Base class.

In development mode, the application starts without requiring PostgreSQL.
The database URL is read from the DATABASE_URL environment variable.
"""

import logging
from typing import Optional, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ------------------------------------------------------------------ #
# Engine & Session Factory                                             #
# ------------------------------------------------------------------ #

_engine = None
_SessionLocal = None


def _get_engine():
    """Lazily create the SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        return _engine

    db_url = settings.DATABASE_URL
    if not db_url:
        logger.warning(
            "DATABASE_URL is not set. Database features will be unavailable. "
            "Set DATABASE_URL in .env to enable PostgreSQL."
        )
        return None

    try:
        # SQLite needs different pool settings (no pool_size/max_overflow)
        is_sqlite = db_url.startswith("sqlite")
        if is_sqlite:
            _engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                echo=settings.DEBUG,
            )
        else:
            _engine = create_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=settings.DEBUG,
            )
        # Test connection
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database engine created successfully: %s", db_url.split("@")[-1] if "@" in db_url else db_url[:30])
        return _engine
    except Exception as e:
        logger.warning(
            "Could not connect to database: %s. "
            "Application will run without database features.",
            str(e),
        )
        _engine = None
        return None


def get_session_factory():
    """Return the sessionmaker, creating the engine if needed."""
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal

    engine = _get_engine()
    if engine is None:
        return None

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db() -> Generator[Optional[Session], None, None]:
    """
    FastAPI dependency that yields a database session.

    Usage in a route:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    factory = get_session_factory()
    if factory is None:
        yield None
        return

    db = factory()
    try:
        yield db
    finally:
        db.close()


def is_database_available() -> bool:
    """Check if the database is reachable."""
    engine = _get_engine()
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def create_all_tables() -> bool:
    """Create all tables defined by ORM models. Returns True on success."""
    engine = _get_engine()
    if engine is None:
        logger.warning("Cannot create tables — no database engine available.")
        return False
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully.")
        return True
    except Exception as e:
        logger.error("Failed to create database tables: %s", str(e))
        return False
