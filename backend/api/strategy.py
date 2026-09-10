"""
backend/api/strategy.py

FastAPI router for Strategy Engine endpoints.
"""

from fastapi import APIRouter, HTTPException
from backend.schemas.strategy import StrategyRequest, StrategyRecommendation
from backend.strategy.engine import recommend_strategy
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/strategy",
    tags=["Strategy Engine"],
)


@router.post(
    "/recommend",
    response_model=StrategyRecommendation,
    summary="Get pit-stop strategy recommendation",
)
async def get_strategy_recommendation(request: StrategyRequest) -> StrategyRecommendation:
    """
    Generate a pit-stop strategy recommendation based on current race state.

    Uses rule-based logic derived from historical F1 compound performance data.
    """
    try:
        result = recommend_strategy(
            driver=request.driver,
            circuit=request.circuit,
            current_lap=request.current_lap,
            total_laps=request.total_laps,
            current_compound=request.current_compound,
            tire_age=request.tire_age,
            position=request.position,
            air_temp=request.air_temp,
            track_temp=request.track_temp,
            rainfall=request.rainfall,
        )
        return StrategyRecommendation(**result)
    except Exception as e:
        logger.error("Strategy recommendation error: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Strategy engine error: {str(e)}")


@router.get("/compounds", summary="Get compound performance reference data")
async def get_compound_reference():
    """Return historical compound performance reference data."""
    from backend.strategy.engine import COMPOUND_STINT_REFERENCE
    return {
        "compounds": COMPOUND_STINT_REFERENCE,
        "disclaimer": "Historical averages from 2022-2024 seasons. Actual performance varies by circuit and conditions.",
    }
