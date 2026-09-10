"""
backend/api/export.py

FastAPI APIRouter for Dataset and Strategy Report Export endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse, FileResponse

from backend.services.export_service import export_session_raw_data
from backend.services.preprocessing_service import preprocess_laps, save_processed_data
from backend.services.pdf_report_service import generate_race_report_html
from backend.services.f1_data_service import get_session_summary, get_driver_classification, get_lap_data
from backend.strategy.engine import recommend_strategy
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/export",
    tags=["Export & Reports"],
)


@router.post("/raw", summary="Export raw session CSV files")
async def export_raw(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Extract FastF1 telemetry and save raw CSV files into data/raw/."""
    try:
        result = export_session_raw_data(year, race, session)
        return {"status": "success", "export": result}
    except Exception as e:
        logger.error("Raw export error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/processed", summary="Export processed Parquet file")
async def export_processed(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
) -> Dict[str, Any]:
    """Run preprocessing pipeline and save Parquet file into data/processed/."""
    try:
        laps = get_lap_data(year, race, session)
        if not laps:
            raise HTTPException(status_code=404, detail="No lap data found.")
        df_proc = preprocess_laps(laps)
        filepath = save_processed_data(df_proc, year, race, session, label="laps")
        return {"status": "success", "saved_parquet": filepath, "record_count": len(df_proc)}
    except Exception as e:
        logger.error("Processed export error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/report", response_class=HTMLResponse, summary="Download HTML Race Strategy Report")
async def export_report_html(
    year: int = Query(...),
    race: str = Query(...),
    session: str = Query("R"),
    driver: str = Query("VER"),
) -> Response:
    """Generate and return styled HTML race strategy report."""
    try:
        summary = get_session_summary(year, race, session)
        drivers = get_driver_classification(year, race, session)
        
        # Recommendation for top driver
        strat = recommend_strategy(
            driver=driver,
            circuit=summary.get("Circuit", "Grand Prix Track"),
            current_lap=20,
            total_laps=57,
            current_compound="MEDIUM",
            tire_age=15,
            track_temp=summary.get("TrackTemp", 38.0),
        )

        html_content = generate_race_report_html(summary, drivers, strat)
        return HTMLResponse(content=html_content, status_code=200)

    except Exception as e:
        logger.error("Report generation error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Report error: {str(e)}")
