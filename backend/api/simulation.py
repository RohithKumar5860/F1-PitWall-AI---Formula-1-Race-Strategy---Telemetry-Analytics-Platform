"""
backend/api/simulation.py

FastAPI router for the What-If Race Simulator.
"""

from fastapi import APIRouter, HTTPException
from backend.schemas.simulation import SimulationRequest, SimulationResult
from backend.simulation.simulator import compare_strategies
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/simulation",
    tags=["Simulator"],
)


@router.post(
    "/compare",
    response_model=SimulationResult,
    summary="Compare two race strategies",
)
async def compare_two_strategies(request: SimulationRequest) -> SimulationResult:
    """
    Run a what-if simulation comparing two race strategies.

    Estimates total race time using simplified tire degradation curves
    and pit stop time loss. Results are clearly labeled as model-based
    estimates, not real race predictions.
    """
    try:
        stints_a = [{"compound": s.compound, "stint_length": s.stint_length} for s in request.strategy_a.stints]
        stints_b = [{"compound": s.compound, "stint_length": s.stint_length} for s in request.strategy_b.stints]

        result = compare_strategies(
            circuit=request.circuit,
            total_laps=request.total_laps,
            base_lap_time=request.base_lap_time,
            pit_loss_seconds=request.pit_loss_seconds,
            strategy_a_name=request.strategy_a.name,
            strategy_a_stints=stints_a,
            strategy_b_name=request.strategy_b.name,
            strategy_b_stints=stints_b,
        )

        return SimulationResult(**result)
    except Exception as e:
        logger.error("Simulation error: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Simulation error: {str(e)}")
