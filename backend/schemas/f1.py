"""
backend/schemas/f1.py

Pydantic v2 response models for Formula One data endpoints.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Season & Schedule                                                    #
# ------------------------------------------------------------------ #

class SeasonListResponse(BaseModel):
    """Response model for GET /f1/seasons."""
    seasons: List[int] = Field(..., description="List of available season years")


class EventScheduleItem(BaseModel):
    """Single event in a season schedule."""
    RoundNumber: Optional[int] = None
    EventName: str = ""
    Country: str = ""
    Location: str = ""
    EventDate: Optional[str] = None
    EventFormat: str = "conventional"


class ScheduleResponse(BaseModel):
    """Response model for GET /f1/seasons/{year}/schedule."""
    year: int
    events: List[EventScheduleItem] = []


# ------------------------------------------------------------------ #
# Session Summary                                                      #
# ------------------------------------------------------------------ #

class SessionSummaryResponse(BaseModel):
    """Response model for GET /f1/session/summary."""
    EventName: str = ""
    Circuit: str = ""
    Country: str = ""
    Date: Optional[str] = None
    SessionName: str = ""
    Year: int = 0
    WeatherAvailable: bool = False
    DriverCount: int = 0
    LapCount: int = 0


# ------------------------------------------------------------------ #
# Driver Classification                                                #
# ------------------------------------------------------------------ #

class DriverClassificationItem(BaseModel):
    """Single driver result entry."""
    DriverCode: str = ""
    DriverNumber: str = ""
    FullName: str = ""
    TeamName: str = ""
    Position: Optional[float] = None
    GridPosition: Optional[float] = None
    Status: str = ""
    Points: Optional[float] = None


# ------------------------------------------------------------------ #
# Lap Data                                                             #
# ------------------------------------------------------------------ #

class LapDataItem(BaseModel):
    """Single lap timing record."""
    Driver: str = ""
    DriverNumber: str = ""
    LapNumber: Optional[int] = None
    LapTimeSeconds: Optional[float] = None
    Sector1Seconds: Optional[float] = None
    Sector2Seconds: Optional[float] = None
    Sector3Seconds: Optional[float] = None
    Stint: Optional[int] = None
    Compound: str = "UNKNOWN"
    TyreLife: Optional[float] = None
    FreshTyre: Optional[bool] = None
    PitInTime: Optional[float] = None
    PitOutTime: Optional[float] = None
    TrackStatus: str = ""
    Position: Optional[float] = None
    Deleted: Optional[bool] = None


# ------------------------------------------------------------------ #
# Tire Data                                                            #
# ------------------------------------------------------------------ #

class TireDataItem(BaseModel):
    """Single tire stint record."""
    Driver: str = ""
    LapNumber: Optional[int] = None
    Stint: Optional[int] = None
    Compound: str = "UNKNOWN"
    TyreLife: Optional[float] = None
    FreshTyre: Optional[bool] = None


# ------------------------------------------------------------------ #
# Pit Stop Data                                                        #
# ------------------------------------------------------------------ #

class PitStopDataItem(BaseModel):
    """Single pit stop transition record."""
    Driver: str = ""
    PitLap: Optional[int] = None
    IncomingCompound: str = "UNKNOWN"
    OutgoingCompound: str = "UNKNOWN"
    Stint: Optional[int] = None
    PitInTime: Optional[float] = None
    PitOutTime: Optional[float] = None


# ------------------------------------------------------------------ #
# Weather Data                                                         #
# ------------------------------------------------------------------ #

class WeatherDataItem(BaseModel):
    """Single weather observation record."""
    Time: Optional[float] = None
    AirTemp: Optional[float] = None
    Humidity: Optional[float] = None
    Pressure: Optional[float] = None
    Rainfall: Optional[Any] = None
    TrackTemp: Optional[float] = None
    WindDirection: Optional[float] = None
    WindSpeed: Optional[float] = None
