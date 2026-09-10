"""
backend/schemas/simulation.py

Pydantic v2 models for the What-If Race Simulator API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class StintDefinition(BaseModel):
    """A single stint within a race strategy."""
    compound: str = Field(..., description="Tire compound (SOFT, MEDIUM, HARD, INTERMEDIATE, WET)")
    stint_length: int = Field(..., ge=1, description="Number of laps on this compound")


class SimulationStrategy(BaseModel):
    """A full race strategy consisting of ordered stints."""
    name: str = Field(..., description="Strategy label (e.g. 'Strategy A')")
    stints: List[StintDefinition] = Field(..., min_length=1, description="Ordered list of stints")


class SimulationRequest(BaseModel):
    """Input for a two-strategy comparison simulation."""
    circuit: str = Field(..., description="Circuit / event name")
    total_laps: int = Field(..., ge=1, description="Total scheduled race laps")
    base_lap_time: float = Field(..., gt=0, description="Baseline lap time in seconds (e.g. 93.5)")
    pit_loss_seconds: float = Field(default=22.0, gt=0, description="Time lost per pit stop in seconds")
    strategy_a: SimulationStrategy
    strategy_b: SimulationStrategy


class StintResult(BaseModel):
    """Simulated result for a single stint."""
    stint_number: int
    compound: str
    stint_length: int
    avg_lap_time: float
    total_stint_time: float
    degradation_per_lap: float


class SimulationStrategyResult(BaseModel):
    """Full simulation output for one strategy."""
    name: str
    total_race_time: float = Field(..., description="Total estimated race time in seconds")
    total_race_time_formatted: str = Field(..., description="Formatted as mm:ss.sss")
    pit_stops: int
    total_pit_loss: float
    stints: List[StintResult]


class SimulationResult(BaseModel):
    """Combined output comparing two strategies."""
    circuit: str
    total_laps: int
    strategy_a: SimulationStrategyResult
    strategy_b: SimulationStrategyResult
    time_delta: float = Field(..., description="Time difference in seconds (A - B, negative means A is faster)")
    time_delta_formatted: str
    faster_strategy: str = Field(..., description="Name of the faster strategy")
    disclaimer: str = Field(
        default="Model-based estimate using simplified degradation curves. Not a real race prediction.",
        description="Simulation disclaimer"
    )
