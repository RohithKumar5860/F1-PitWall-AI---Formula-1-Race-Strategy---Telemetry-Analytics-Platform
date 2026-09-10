"""
backend/schemas/strategy.py

Pydantic v2 models for the Strategy Engine API.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class StrategyRequest(BaseModel):
    """Input parameters for a strategy recommendation."""
    driver: str = Field(..., description="Driver 3-letter code (e.g. VER)")
    circuit: str = Field(..., description="Circuit / event name")
    current_lap: int = Field(..., ge=1, description="Current race lap number")
    total_laps: int = Field(..., ge=1, description="Total scheduled race laps")
    current_compound: str = Field(..., description="Current tire compound (SOFT, MEDIUM, HARD, INTERMEDIATE, WET)")
    tire_age: int = Field(..., ge=0, description="Laps completed on current tire set")
    position: Optional[int] = Field(None, ge=1, description="Current race position")
    air_temp: Optional[float] = Field(None, description="Air temperature in °C")
    track_temp: Optional[float] = Field(None, description="Track temperature in °C")
    rainfall: Optional[bool] = Field(False, description="Whether it is currently raining")


class StrategyRecommendation(BaseModel):
    """Output from the strategy engine."""
    recommended_pit_window: str = Field(..., description="Recommended lap range for pit stop, e.g. 'Lap 22-26'")
    suggested_compound: str = Field(..., description="Suggested next tire compound")
    estimated_stint_length: int = Field(..., description="Recommended stint length in laps")
    urgency: str = Field(..., description="LOW, MEDIUM, or HIGH urgency rating")
    explanation: str = Field(..., description="Human-readable reasoning behind the recommendation")
    alternative_strategy: Optional[str] = Field(None, description="Alternative approach if available")
    disclaimer: str = Field(
        default="Rule-based estimate using historical averages. Not a real-time race prediction.",
        description="Model disclaimer"
    )
