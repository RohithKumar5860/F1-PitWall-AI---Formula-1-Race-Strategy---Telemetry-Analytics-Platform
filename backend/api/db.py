"""
backend/api/db.py

FastAPI APIRouter for Database Management endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db, is_database_available, create_all_tables
from backend.services.db_service import sync_session_to_db, get_stored_races
from backend.services.f1_data_service import get_driver_classification, get_lap_data, get_tire_data, get_pitstop_data, get_weather_data
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/db",
    tags=["Database"],
)


@router.get("/status", summary="Get database connection status")
async def db_status() -> Dict[str, Any]:
    """Check if PostgreSQL database connection is active."""
    available = is_database_available()
    return {
        "database_connected": available,
        "mode": "PostgreSQL" if available else "In-Memory / File-based",
    }


@router.post("/init", summary="Initialize database tables")
async def init_tables() -> Dict[str, Any]:
    """Create all ORM database tables."""
    success = create_all_tables()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize database tables. Ensure DATABASE_URL is set correctly."
        )
    return {"status": "success", "message": "Database tables initialized."}


@router.post("/sync", summary="Sync FastF1 session data into database")
async def sync_session(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Sync session telemetry data from FastF1 into PostgreSQL database."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. DATABASE_URL is not set."
        )

    try:
        drivers = get_driver_classification(year, race, session)
        laps = get_lap_data(year, race, session)
        tires = get_tire_data(year, race, session)
        pitstops = get_pitstop_data(year, race, session)
        weather = get_weather_data(year, race, session)

        result = sync_session_to_db(
            db=db,
            year=year,
            race_name=race,
            session_type=session,
            drivers_data=drivers,
            laps_data=laps,
            tires_data=tires,
            pitstops_data=pitstops,
            weather_data=weather,
        )
        return {"status": "success", "synced": result}
    except Exception as e:
        logger.error("DB sync failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Database sync failed: {str(e)}")


@router.get("/races", summary="List stored races from database")
async def list_stored_races(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve list of races stored in the database."""
    if db is None:
        return {"races": [], "message": "Database not connected."}

    races = get_stored_races(db)
    return {"count": len(races), "races": races}
