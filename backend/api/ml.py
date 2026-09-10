"""
backend/api/ml.py

FastAPI APIRouter for Machine Learning models and inference endpoints.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.services.ml_service import (
    train_all_models,
    get_models_status,
    predict_lap_time,
    predict_tire_degradation,
    predict_pit_window,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


class LapTimePredictRequest(BaseModel):
    compound: str = Field("MEDIUM", description="Tire compound (SOFT, MEDIUM, HARD)")
    tyre_life: int = Field(10, description="Laps on current tire set")
    lap_number: int = Field(15, description="Current race lap number")
    total_laps: int = Field(57, description="Total race laps")
    stint: int = Field(1, description="Stint number")


class TireDegPredictRequest(BaseModel):
    compound: str = Field("MEDIUM", description="Tire compound")
    tyre_life: int = Field(15, description="Laps on current tire set")
    stint: int = Field(1, description="Stint number")
    lap_number: int = Field(15, description="Lap number")


class PitWindowPredictRequest(BaseModel):
    compound: str = Field("SOFT", description="Tire compound")
    tyre_life: int = Field(18, description="Laps on current tire set")
    current_lap: int = Field(18, description="Current race lap")
    total_laps: int = Field(57, description="Total race laps")
    stint: int = Field(1, description="Stint number")
    recent_pace: float = Field(90.5, description="Avg lap time over last 5 laps")
    pace_dropoff: float = Field(0.6, description="Pace dropoff compared to stint start")


@router.get("/models", summary="Get ML models status & metrics")
async def list_models() -> Dict[str, Any]:
    """Return training status, metrics, and feature lists for all ML models."""
    return get_models_status()


@router.post("/train", summary="Train all ML models")
async def train_models() -> Dict[str, Any]:
    """Train all 3 ML models (LapTime, TireDegradation, PitWindow) and save to disk."""
    try:
        metrics = train_all_models()
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        logger.error("Model training failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/predict/lap-time", summary="Predict lap time (XGBoost)")
async def predict_lap_time_endpoint(req: LapTimePredictRequest) -> Dict[str, Any]:
    """Predict expected lap time using XGBoost model."""
    try:
        return predict_lap_time(
            tyre_life=req.tyre_life,
            compound=req.compound,
            lap_number=req.lap_number,
            total_laps=req.total_laps,
            stint=req.stint,
        )
    except Exception as e:
        logger.error("Lap time prediction error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict/tire-degradation", summary="Predict tire degradation (GradientBoosting)")
async def predict_tire_deg_endpoint(req: TireDegPredictRequest) -> Dict[str, Any]:
    """Predict tire degradation pace loss per lap using GradientBoosting model."""
    try:
        return predict_tire_degradation(
            compound=req.compound,
            tyre_life=req.tyre_life,
            stint=req.stint,
            lap_number=req.lap_number,
        )
    except Exception as e:
        logger.error("Tire deg prediction error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict/pit-window", summary="Predict pit stop window (RandomForest)")
async def predict_pit_window_endpoint(req: PitWindowPredictRequest) -> Dict[str, Any]:
    """Predict optimal pit window range and confidence using RandomForest model."""
    try:
        return predict_pit_window(
            compound=req.compound,
            tyre_life=req.tyre_life,
            current_lap=req.current_lap,
            total_laps=req.total_laps,
            stint=req.stint,
            recent_pace=req.recent_pace,
            pace_dropoff=req.pace_dropoff,
        )
    except Exception as e:
        logger.error("Pit window prediction error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
