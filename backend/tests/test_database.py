"""
backend/tests/test_database.py

Unit tests for database models, connection, and sync operations.
Uses an in-memory SQLite engine for fast, isolated testing.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base
from backend.models.f1_models import Race, Driver, Team, LapTime
from backend.services.db_service import sync_session_to_db, get_stored_races


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_sync_session_to_db(in_memory_db):
    drivers_data = [{"DriverCode": "VER", "FullName": "Max Verstappen", "DriverNumber": 1}]
    laps_data = [{"Driver": "VER", "LapNumber": 1, "LapTimeSeconds": 94.5, "Compound": "SOFT", "TyreLife": 1, "Stint": 1}]
    
    result = sync_session_to_db(
        db=in_memory_db,
        year=2024,
        race_name="Bahrain Grand Prix",
        session_type="R",
        drivers_data=drivers_data,
        laps_data=laps_data,
    )

    assert result["synced_drivers"] == 1
    assert result["synced_laps"] == 1

    stored_races = get_stored_races(in_memory_db)
    assert len(stored_races) == 1
    assert stored_races[0]["event_name"] == "Bahrain Grand Prix"
