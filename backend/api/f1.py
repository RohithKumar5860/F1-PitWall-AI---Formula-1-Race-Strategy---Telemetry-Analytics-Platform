"""
backend/api/f1.py

FastAPI APIRouter exposing Formula One historical session data endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from backend.services.f1_data_service import (
    get_available_seasons,
    get_season_schedule,
    get_session_summary,
    get_driver_classification,
    get_lap_data,
    get_tire_data,
    get_pitstop_data,
    get_weather_data,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/f1",
    tags=["Formula One"],
)


@router.get("/seasons", summary="Get supported F1 seasons")
async def list_seasons() -> Dict[str, Any]:
    """Return list of supported Formula One season years."""
    seasons = get_available_seasons()
    return {"seasons": seasons}


@router.get("/seasons/{year}/schedule", summary="Get event schedule for a season")
async def get_schedule(year: int) -> Dict[str, Any]:
    """Retrieve event schedule for a specified year."""
    seasons = get_available_seasons()
    if year not in seasons and (year < 1950 or year > 2030):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Season {year} is out of supported range (1950-2030)."
        )
    try:
        schedule = get_season_schedule(year)
        return {"year": year, "events": schedule}
    except Exception as e:
        logger.error("Failed to fetch schedule for %d: %s", year, str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not load schedule for season {year}: {str(e)}"
        )


@router.get("/session/summary", summary="Get session summary")
async def session_summary(
    year: int = Query(..., description="Season year, e.g. 2024"),
    race: str = Query(..., description="Event name, e.g. Monaco"),
    session: str = Query("R", description="Session type code (FP1, FP2, FP3, Q, SQ, S, R)"),
) -> Dict[str, Any]:
    """Return high-level metadata for a session."""
    try:
        summary = get_session_summary(year, race, session)
        return summary
    except Exception as e:
        logger.error("Session summary error (%d, %s, %s): %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load session summary for '{race}' ({year}, {session}): {str(e)}"
        )


@router.get("/session/drivers", summary="Get driver classification")
async def session_drivers(
    year: int = Query(..., description="Season year"),
    race: str = Query(..., description="Event name"),
    session: str = Query("R", description="Session type code"),
) -> List[Dict[str, Any]]:
    """Return driver results and classification for a session."""
    try:
        drivers = get_driver_classification(year, race, session)
        return drivers
    except Exception as e:
        logger.error("Session drivers error (%d, %s, %s): %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load driver data: {str(e)}"
        )


@router.get("/session/laps", summary="Get lap timing data")
async def session_laps(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
    driver: Optional[str] = Query(None, description="Filter by driver 3-letter code (e.g. VER)"),
) -> List[Dict[str, Any]]:
    """Return lap-by-lap timing data for a session, optionally filtered by driver."""
    try:
        laps = get_lap_data(year, race, session, driver=driver)
        return laps
    except Exception as e:
        logger.error("Session laps error (%d, %s, %s): %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load lap data: {str(e)}"
        )


@router.get("/session/tires", summary="Get tire compound and stint life data")
async def session_tires(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> List[Dict[str, Any]]:
    """Return tire compound and stint life records for a session."""
    try:
        tires = get_tire_data(year, race, session)
        return tires
    except Exception as e:
        logger.error("Session tires error (%d, %s, %s): %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load tire data: {str(e)}"
        )


@router.get("/session/pitstops", summary="Get pit stop and stint transition data")
async def session_pitstops(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> List[Dict[str, Any]]:
    """Return pit stop stint transition records for a session."""
    try:
        pitstops = get_pitstop_data(year, race, session)
        return pitstops
    except Exception as e:
        logger.error("Session pitstops error (%d, %s, %s): %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load pit stop data: {str(e)}"
        )


@router.get("/session/weather", summary="Get weather observation data")
async def session_weather(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> List[Dict[str, Any]]:
    """Return weather telemetry records for a session."""
    try:
        weather = get_weather_data(year, race, session)
        return weather
    except Exception as e:
        logger.error("Session weather error (%d, %s, %s): %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load weather data: {str(e)}"
        )


@router.post("/session/preprocess", summary="Preprocess and feature-engineer session lap data")
async def preprocess_session(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
    save_parquet: bool = Query(True, description="Whether to save result to Parquet file"),
) -> Dict[str, Any]:
    """Run data cleaning and feature engineering pipeline on session lap data."""
    try:
        from backend.services.preprocessing_service import preprocess_laps, save_processed_data
        laps = get_lap_data(year, race, session)
        if not laps:
            raise HTTPException(status_code=404, detail="No lap data found for specified session.")
        
        df_processed = preprocess_laps(laps)
        records = df_processed.to_dict(orient="records")
        
        saved_path = None
        if save_parquet and not df_processed.empty:
            saved_path = save_processed_data(df_processed, year, race, session, label="laps")

        return {
            "year": year,
            "race": race,
            "session": session,
            "total_raw_laps": len(laps),
            "total_processed_laps": len(df_processed),
            "feature_count": len(df_processed.columns),
            "feature_names": list(df_processed.columns),
            "saved_parquet": saved_path,
            "sample_records": records[:5],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Preprocessing failed for %d %s %s: %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preprocessing failed: {str(e)}"
        )


@router.get("/session/processed", summary="Get preprocessed lap data")
async def session_processed_laps(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> List[Dict[str, Any]]:
    """Return feature-engineered preprocessed lap data for a session."""
    try:
        from backend.services.preprocessing_service import preprocess_laps
        laps = get_lap_data(year, race, session)
        df_processed = preprocess_laps(laps)
        return df_processed.to_dict(orient="records")
    except Exception as e:
        logger.error("Session processed laps error (%d, %s, %s): %s", year, race, session, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load processed lap data: {str(e)}"
        )

